import gmplot

class HTMLgenerator(gmplot.GoogleMapPlotter):
    def __init__(self, center_lat, center_lng, zoom, apikey='',
                 map_type='satellite', tilt=0):
        super(HTMLgenerator, self).__init__(center_lat, center_lng, zoom, apikey)

        self.map_type = map_type
        self.tilt = tilt
        assert(self.map_type in ['roadmap', 'satellite', 'hybrid', 'terrain'])
        assert(self.tilt in [0, 45])

    def write_map(self,  f):
        f.write('\t\tvar centerlatlng = new google.maps.LatLng(%f, %f);\n' %
                (self.center[0], self.center[1]))
        f.write('\t\tvar myOptions = {\n')
        f.write('\t\t\tzoom: %d,\n' % (self.zoom))
        f.write('\t\t\tcenter: centerlatlng,\n')

        # These are the only changes (override)
        f.write('\t\t\tmapTypeId: \'%s\',\n' % (self.map_type))
        f.write('\t\t\ttilt: %d\n' % (self.tilt))

        f.write('\t\t};\n')
        f.write(
            '\t\tmap = new google.maps.Map(document.getElementById("map_canvas"), myOptions);\n')
        f.write('\n')

    
    # All uavs must have marker title that starts with "UAV", ie. "UAV1"

    def write_point(self, f, lat, lon, color, title):
        f.write('\t\tvar latlng = new google.maps.LatLng(%f, %f);\n' %
                (lat, lon))
        f.write('\t\tvar img = new google.maps.MarkerImage(\'%s\');\n' %
                (self.coloricon % color))
        f.write('\t\tvar marker = new google.maps.Marker({\n')
        f.write('\t\t\ttitle: "%s",\n' % title)
        f.write('\t\t\ticon: img,\n')
        f.write('\t\t\tposition: latlng\n')
        f.write('\t\t});\n')
        f.write('\t\tmarker.setMap(map);\n')
        # these are the only changes (override)
        if title.startswith("UAV"):
            f.write('\t\tmarkers_uav.push(marker);\n')   
        else:
            f.write('\t\tmarkers.push(marker);\n')
        f.write('\n')

    def write_polygon(self, f, path, settings):
        clickable = False
        geodesic = True
        strokeColor = settings.get('edge_color') or settings.get('color')
        strokeOpacity = settings.get('edge_alpha')
        strokeWeight = settings.get('edge_width')
        fillColor = settings.get('face_color') or settings.get('color')
        fillOpacity= settings.get('face_alpha')
        f.write('\t\tvar coords = [\n')
        for coordinate in path:
            f.write('\t\t\tnew google.maps.LatLng(%f, %f),\n' %
                    (coordinate[0], coordinate[1]))
        f.write('\t\t];\n')
        f.write('\n')

        f.write('\t\tpolygon = new google.maps.Polygon({\n')
        f.write('\t\t\tclickable: %s,\n' % (str(clickable).lower()))
        f.write('\t\t\tgeodesic: %s,\n' % (str(geodesic).lower()))
        f.write('\t\t\tfillColor: "%s",\n' % (fillColor))
        f.write('\t\t\tfillOpacity: %f,\n' % (fillOpacity))
        f.write('\t\t\tpaths: coords,\n')
        f.write('\t\t\tstrokeColor: "%s",\n' % (strokeColor))
        f.write('\t\t\tstrokeOpacity: %f,\n' % (strokeOpacity))
        f.write('\t\t\tstrokeWeight: %d\n' % (strokeWeight))
        f.write('\t\t});\n')
        f.write('\n')
        f.write('\t\tpolygon.setMap(map);\n')
        f.write('\n\n')


    def write_mouseListener(self, f):
        f.write("\t\tmap.addListener('mousemove', function (event) {\n")
        f.write('\t\t\tdocument.title = JSON.stringify(event.latLng.toJSON());\n')
        f.write('\t\t})\n\n')

    def write_polygonDragListener(self, f):
        f.write("\t\tpolygon.addListener('drag', function() {\n")
        f.write('\t\t\tvar polypath = polygon.getPath().getArray();\n')
        f.write('\t\t\tfor(var i = 0; i < polypath.length; i++){\n')
        f.write('\t\t\t\tmarkers[i].setPosition(polypath[i]);\n')
        f.write('\t\t\t}\n')
        f.write('\t\t})\n\n')

    # create the html file which include one google map and all points and
    # paths
    def draw(self, htmlfile):
        f = open(htmlfile, 'w')
        f.write('<html>\n')
        f.write('<head>\n')
        f.write(
            '<meta name="viewport" content="initial-scale=1.0, user-scalable=no" />\n')
        f.write(
            '<meta http-equiv="content-type" content="text/html; charset=UTF-8"/>\n')
        f.write('<title>Google Maps - pygmaps </title>\n')
        if self.apikey:
            f.write('<script defer type="text/javascript" src="https://maps.googleapis.com/maps/api/js?libraries=visualization&sensor=true_or_false&key=%s"></script>\n' % self.apikey )
        else:
            f.write('<script defer type="text/javascript" src="https://maps.googleapis.com/maps/api/js?libraries=visualization&sensor=true_or_false"></script>\n' )

        f.write('<script type="text/javascript">\n')
        f.write('\tvar markers = [];\n')
        f.write('\tvar markers_uav = [];\n')
        f.write('\tvar polygon;\n')
        f.write('\tvar map;\n\n')
        f.write('\tfunction initialize() {\n')
        self.write_map(f)
        # self.write_grids(f)
        # self.write_points(f)
        # self.write_paths(f)
        # self.write_shapes(f)
        # self.write_heatmap(f)

        # these are the only changes (override)
        # self.write_mouseListener(f)
        # self.write_polygonDragListener(f)

        f.write('\t}\n')
        f.write('</script>\n')
        f.write('</head>\n')
        f.write(
            '<body style="margin:0px; padding:0px;" onload="initialize()">\n')
        f.write(
            '\t<div id="map_canvas" style="width: 100%; height: 100%;"></div>\n')
        f.write('</body>\n')
        f.write('</html>\n')
        f.close()

class GoogleMapsJSWrapper:
    def __init__(self, map_holder):
        self.js_code = ""
        self.map_holder = map_holder
    
    def add_markers(self, coords):
        for coord in coords:
            self.js_code += "var latlng = new google.maps.LatLng(%f, %f);" % (coord[1], coord[0])
            self.js_code += \
                '''
                var img = new google.maps.MarkerImage('/home/ivan/.local/lib/python2.7/site-packages/gmplot/markers/FF0000.png');
                var marker = new google.maps.Marker({
                    title: "no implementation",
                    icon: img,
                    position: latlng
                });
                marker.setMap(map);
                markers.push(marker);
                '''

    def add_polygon(self, coords):
        self.js_code += "var coords = [\n"
        for coord in coords:
            self.js_code += "\tnew google.maps.LatLng(%f, %f),\n" % (coord[1], coord[0])
        self.js_code += "];\n"

        self.js_code += \
            '''
            polygon = new google.maps.Polygon({
                clickable: false, 	// onemogucuje prikaz koordinata, draggable ne radi bez toga
                geodesic: true,
                fillColor: "#6495ED",
                fillOpacity: 0.300000,
                paths: coords,
                strokeColor: "#6495ED",
                strokeOpacity: 1.000000,
                strokeWeight: 1,
                draggable: true
            });

            polygon.setMap(map);
            '''

    def clear_map(self):
        self.js_code += \
            '''
            for(var i = 0; i < markers.length; i++){
                markers[i].setMap(null);
            }
            markers = [];

            if(polygon != null){
                polygon.setMap(null);
            }
            '''
        
    def set_map(self, center_coords, zoom):
        self.js_code += "var centerlatlng = new google.maps.LatLng(%f, %f);" % (center_coords[1], center_coords[0])
        self.js_code += "map.setCenter(centerlatlng);"
        self.js_code += "map.setZoom(%d);" % zoom

    
    def execute(self):
        self.map_holder.run_javascript(self.js_code)
        self.js_code = ""


# gmap=HTMLgenerator(40.414619186803854, -3.712474573081552, 19)
gmap=HTMLgenerator(0, 0, 1)

# latitude_list = [ 17.4567417, 17.5587901, 17.6245545]
# longitude_list = [ 78.2913637, 78.007699, 77.9266135 ]
# longitude_list, latitude_list = zip(*[(-3.712474573081552, 40.414619186803854), (-3.712463167623644, 40.4145659235525), (-3.713247830511171, 40.41446838255727), (-3.7132582918029717, 40.41452147137448), (-3.7133139823755648, 40.41480599373001), (-3.7133391511777996, 40.41493475784219), (-3.712563736835892, 40.41503800824957), (-3.712515491263675, 40.414810917348746), (-3.712474573081552, 40.414619186803854)])
# gmap.scatter( latitude_list, longitude_list, color='#FF0000', size = 100, marker = True)
# gmap.polygon(latitude_list, longitude_list, color = 'cornflowerblue')

# uav_long, uav_lat = -3.712474573091552, 40.414618186903854
# gmap.marker( uav_lat, uav_long, color='#0000FF', title='UAV1')

# API KEY
gmap.apikey = "AIzaSyAvFZ4xali0KK8Qh-XRs8Wsbbaj7CktBag"
gmap.draw("map.html")

