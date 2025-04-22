
// // Initialize the map
// // Initialize the map
// // var map = L.map('map').setView([33.8797696, -117.8881295], 13);

// var user_location = fetch('/static/file.json')
//                         .then(response => response.json())
//                         .then(data => {
//                             [data.user_latitude, data.user_longitude]
//                         })

var map = L.map('map').setView([33.88092675, -117.90412475], 12); 
// var map = L.map('map').setView(user_location, 12); 

// // Add a tile layer (OpenStreetMap)
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; OpenStreetMap contributors'
}).addTo(map);

// // Add a marker
// var marker = 
// L.marker([33.8820839, -177.8884284]).addTo(map).bindPopup("Disneyland");
// L.marker([33.8797696, -117.8881295]).addTo(map).bindPopup("CSUF").openPopup();


// L.marker([33.816553,-117.92012]).addTo(map).bindPopup("I am a red leaf.");
// L.marker([33.8797696, -117.8881295]).addTo(map).bindPopup("I am an orange leaf.");
// L.marker([33.881, -117.8882]).addTo(map).bindPopup("I am a green leaf.");

fetch('/static/file.json')  // adjust the path to where your JSON file is
  .then(response => response.json())
  .then(data => {
    // data.forEach(loc=>{
    L.marker([data.latitude, data.longitude])
        .addTo(map);
        // .bindPopup(loc.address);
    });
    // console.log(data); // Do something with your JSON data
//   })
//   .catch(error => {
//     console.error('Error loading JSON:', error);
//   });


// fetch("/map_front/") // Adjust endpoint as needed
//     .then(response => response.json())
//     .then(data => {
//         data.locations.forEach(loc => {
//             L.marker([loc.latitude, loc.longitude])
//                 .addTo(map)
//                 .bindPopup(loc.address);
//         });
//     })
//     .catch(error => console.error("Error loading map data:", error));


// // Add a popup with an address
// // marker.bindPopup("<b>disney</b><br>disneylad").openPopup();

// var marker = 

// var locations = [
//     { coords: [33.816553,-117.92012], address: "1313 Disneyland Dr, Anaheim, CA 92802" },
//     { coords: [33.8797696,-117.8881295], address: "csuf" }
// ];

// locations.forEach(loc => {
//     L.marker(loc.coords)
//      .addTo(map)
//      .bindPopup(`<b>Address:</b><br>${loc.address}`);
// });

// // fetch('https://nominatim.openstreetmap.org/search?format=json&q=123 Example St, NY')
// //     .then(response => response.json())
// //     .then(data => {
// //         if (data.length > 0) {
// //             var lat = data[0].lat;
// //             var lon = data[0].lon;
// //             L.marker([lat, lon]).addTo(map)
// //              .bindPopup("123 Example St, NY 10001")
// //              .openPopup();
// //         }
// //     });


// // var circle = L.circle([51.508, -0.11], {
// //     color: 'red',
// //     fillColor: '#f03',
// //     fillOpacity: 0.5,
// //     radius: 500
// // }).addTo(map);




/////////////////////////////////////////////////////////////
// var map = L.map('map').setView([51.505, -0.09], 13);

// L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
//     maxZoom: 19,
//     attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
// }).addTo(map);

// L.marker([51.5, -0.09]).addTo(map)
//         .bindPopup('A pretty CSS popup.<br> Easily customizable.')
//         .openPopup();