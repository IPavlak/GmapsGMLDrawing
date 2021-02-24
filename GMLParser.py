from osgeo import ogr
from osgeo.osr import SpatialReference
import json
from math import sqrt, atan2, pi, sin, cos, radians

earth_a = 6378137.00000         # [m] WGS84 equator radius
earth_b = 6356752.31414         # [m] WGS84 epolar radius
earth_e = 8.1819190842622e-2    #  WGS84 eccentricity
earth_ee = earth_e*earth_e

def ECEFtoWGS84(x, y, z):
    lambd = atan2(y, x)
    l = sqrt((x*x)+(y*y))
    
    phi = atan2(z, (1.0-earth_ee)*l)
    # // iterate to improve accuracy
    for i in range(100):
        db = phi
        n = earth_a / sqrt(1.0 - (earth_ee * sin(phi) * sin(phi)))
        h = l / cos(phi) - n
        phi = atan2(z, (1.0 - earth_ee*n / (n+h)) * l)
        db = abs(db-phi)
        if db < 1e-12:
            break
    if phi > 0.5*pi:
        phi -= pi/2
    
    lat = phi*180/pi
    lon = lambd*180/pi
    return lat, lon, h

def WGS84toECEF(lat, lon, h):
    phi = radians(lat)
    lambd = radians(lon)
    # WGS84 from eccentricity
    l = earth_a / sqrt(1.0 - earth_ee * sin(phi) * sin(phi))
    x = (l + h) * cos(phi) * cos(lambd)
    y = (l + h) * cos(phi) * sin(lambd)
    z = (((1.0 - earth_ee) * l) + h) * sin(phi)

    return x, y, z

def ECEFtoENU(x, y, z, lat0, lon0, h0):
    phi = radians(lat0)
    lambd = radians(lon0)

    # ECEF origin
    x0, y0, z0 = WGS84toECEF(lat0, lon0, h0)

    xd = x - x0
    yd = y - y0
    zd = z - z0

    xEast  =     -sin(lambd)      * xd     +cos(lambd)      * yd      +0     * zd
    yNorth = -cos(lambd)*sin(phi) * xd -sin(lambd)*sin(phi) * yd   +cos(phi) * zd
    zUp    =  cos(lambd)*cos(phi) * xd +cos(phi)*sin(lambd) * yd   +sin(phi) * zd

    return xEast, yNorth, zUp

def ENUtoECEF(x, y, z, lat0, lon0, h0):
    phi = radians(lat0)
    lambd = radians(lon0)

    # ECEF origin
    x0, y0, z0 = WGS84toECEF(lat0, lon0, h0)

    X = -sin(lambd) * x  -cos(lambd)*sin(phi) * y  +cos(lambd)*cos(phi) * z  + x0
    Y =  cos(lambd) * x  -sin(lambd)*sin(phi) * y  +sin(lambd)*cos(phi) * z  + y0
    Z =     0       * x         +cos(phi)     * y        +sin(phi)      * z  + z0

    return X, Y, Z


class GMLParser:
    def __init__(self):
        self.points_dict = {}

    '''
    All functions that start with "getPoints" return list of lists of coordinates
    MultiPolygon and MultiLineString may have few parcels within them (few lists of coordinates)
    while MultiPoint, Polygon and LineString, describe only one parcel (one list of coordinates)

    !!!!! Points are in the form of (Longitude, Latitude) !!!!!
    '''
    def getPointsFromMultipolygon(self, geometry):
        polygonCount = geometry.GetGeometryCount()
        points = []
        for i in range(polygonCount):
            polygon = geometry.GetGeometryRef(i)
            points.append(self.getPointsFromPolygon(polygon)[0])
        return points

    def getPointsFromMultilinestring(self, geometry):         #not sure
        lineStringCount = geometry.GetGeometryCount()
        points = []
        for i in range(lineStringCount):
            lineString = geometry.GetGeometryRef(i)
            points.append(self.getPointsFromLineString(lineString)[0])
        return  [points]

    def getPointsFromPolygon(self, geometry):
        linearRing = geometry.GetGeometryRef(0)
        points = linearRing.GetPoints()
        return [points]

    def getPointsFromLineString(self, geometry):  # not sure
        line = geometry.GetGeometryRef(0)
        points = line.GetPoints()
        return [points]

    def getPointsFromMultipoint(self, geometry):  #not sure
        points = geometry.GetPoints()
        return [points]

    def getPointFromPoint(self, geometry):
        point = (geometry.getX(), geometry.getY())
        return [[point]]

    def getPoints(self, geometry):
        gtype = geometry.GetGeometryType()
        name = geometry.GetGeometryName()
        if gtype == 6 and name == "MULTIPOLYGON":
            return self.getPointsFromMultipolygon(geometry)
        elif gtype == 5 and name == "MULTILINESTRING":  #not sure
            return self.getPointsFromMultilinestring(geometry)
        elif gtype == 4 and name == "MULTIPOINT":       #not sure
            return self.getPointsFromMultipoint(geometry)
        elif gtype == 3 and name == "POLYGON":
            return self.getPointsFromPolygon(geometry)
        elif gtype == 2 and name == "LINESTRING":       #not sure
            return self.getPointsFromLineString(geometry)
        elif gtype == 1 and name == "POINT":            #not sure
            return self.getPointFromPoint(geometry)
        else:
            print("GMLParser: Unrecognized geometry type: ", name)
        return -1


    def getCoordinatesDictionary(self):
        return self.points_dict


    def parse(self, GMLfile):
        ogr.RegisterAll()
        inSource = ogr.Open(GMLfile)
        self.points_dict = {}
        for layerIndex in range(inSource.GetLayerCount()):
            ############################### LAYER #######################################
            inLayer = inSource.GetLayer(layerIndex)
            inLayer.ResetReading()          # not neccessary, ensures iterating from begining

            ############################### FEATURE #####################################
            for featureIndex in range(inLayer.GetFeatureCount()):
                feature = inLayer.GetNextFeature()

            ############################### GEOMETRY #####################################
                geometry = feature.GetGeometryRef()
                coord_system = geometry.GetSpatialReference()

                targetReference = SpatialReference()
                targetReference.ImportFromEPSG(4326) # WGS84
                geometry.TransformTo(targetReference)

                points = self.getPoints(geometry)
                # print(points)

                entryName = "Layer-" + str(layerIndex) + " Feature-" + str(featureIndex)
                self.points_dict[entryName] = points
                if self.points_dict.has_key('coordinates'):
                    self.points_dict['coordinates'] = self.points_dict['coordinates'] + points
                else:
                    self.points_dict['coordinates'] = points


    def exportToJSON(self):
        with open('WGS84_coordinates_from_GML.json', 'w') as file:
            json.dump(self.points_dict, file, indent=4)


if __name__ == '__main__':
    inSource = "/home/ivan/Downloads/katastarski_plan_CESTICE.gml"
    # inSource = /home/ivan/Downloads/Building_9620123VK0192B.gml"
    # inSource = "/home/ivan/Downloads/Building_9531109VK0193B.gml"
    # inSource = "/home/ivan/Downloads/Building_9642901VK3794B.gml"

    parser = GMLParser()
    parser.parse(inSource)
    print(parser.getCoordinatesDictionary())
