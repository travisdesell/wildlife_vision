var map = L.map('map').setView([51.505, -0.09], 13);

L.tileLayer('https://api.tiles.mapbox.com/v4/{id}/{z}/{x}/{y}.png?access_token={accessToken}', {
    attribution: 'Map data &copy; <a href="http://openstreetmap.org">OpenStreetMap</a> contributors, <a href="http://creativecommons.org/licenses/by-sa/2.0/">CC-BY-SA</a>, Imagery © <a href="http://mapbox.com">Mapbox</a>',
    maxZoom: 18,
    id: 'mattinm.cif7hgtnd0kt3solzov65xjfv',
    accessToken: 'pk.eyJ1IjoibWF0dGlubSIsImEiOiJjaWY3aGd1eHYwa3luczdrcmpjM3pvMjk3In0.EfynKXWuvFlSDYWmv4OeGA'
}).addTo(map);

var featureGroup = L.featureGroup().addTo(map);

var drawControl = new L.Control.Draw({
	edit: {
		featureGroup: featureGroup
	}
}).addTo(map);

map.on('draw:created', function(e) {
	featureGroup.addLayer(e.layer);
});