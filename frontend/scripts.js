document.addEventListener('DOMContentLoaded', function () {
  document.getElementById('destinationForm').addEventListener('submit', function (event) {
    event.preventDefault();
    submitDestination();
  });

  document.getElementById('calculateRouteButton').addEventListener('click', function () {
    calculateOptimizedRoute();
  });

  loadDestinations();
});

async function submitDestination() {
  var address = document.getElementById('address').value;
  var deadline = document.getElementById('deadline').value;

  // If address or deadline is not provided, show an alert
  if (!address || !deadline) {
    alert('Please fill in all fields.');
    return;
  }

  // Fetch latitude and longitude from Nominatim API based on the entered address
  try {
    const coordinates = await fetchCoordinatesFromAddress(address);

    if (coordinates) {
      var data = {
        address: address,
        latitude: coordinates.lat,
        longitude: coordinates.lon,
        deadline: deadline
      };

      
      const response = await fetch('http://127.0.0.1:5000/create_destination', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
      });

      // Check the response status
      if (response.status === 201) {
        alert('Drop-point added successfully!');
        loadDestinations();  // Refresh the destinations list after creation
        clearFields();  // Clear the fields only after the destination is created
      } else {
        alert('Failed to add drop-point.');
      }
    } else {
      alert('Failed to get coordinates for the address.');
    }
  } catch (error) {
    console.error('An error occurred:', error);
    alert('An error occurred: ' + error);
  }
}

// Function to fetch coordinates using Nominatim API based on the address
function fetchCoordinatesFromAddress(address) {
  var url = `https://nominatim.openstreetmap.org/search?q=${encodeURIComponent(address)}&format=xml&polygon_kml=1&addressdetails=1`;

  return fetch(url)
    .then(response => response.text())
    .then(data => {
      var parser = new DOMParser();
      var xmlDoc = parser.parseFromString(data, "text/xml");
      var place = xmlDoc.getElementsByTagName('place')[0];

      if (place) {
        var lat = place.getAttribute('lat');
        var lon = place.getAttribute('lon');
        return { lat: lat, lon: lon };
      } else {
        return null;
      }
    })
    .catch(error => {
      console.error('Error fetching coordinates:', error);
      return null;
    });
}

function loadDestinations() {
  fetch('http://127.0.0.1:5000/destinations')
    .then(function (response) {
      if (response.ok) {
        return response.json();
      } else {
        throw new Error('Failed to fetch destinations.');
      }
    })
    .then(function (data) {
      var availableDestinationsContainer = document.getElementById('availableDestinationsContainer');
      availableDestinationsContainer.innerHTML = '';

      data.destinations.forEach(function (dest) {
        var destinationElement = document.createElement('div');
        destinationElement.classList.add('destination');
        destinationElement.innerHTML = `
          <p><strong>ID:</strong> ${dest.id}
          <strong>Address:</strong> ${dest.address}
          <strong>Latitude:</strong> ${dest.latitude}
          <strong>Longitude:</strong> ${dest.longitude}
          <strong>Deadline:</strong> ${dest.deadline}</p>
        `;
        availableDestinationsContainer.appendChild(destinationElement);
      });
    })
    .catch(function (error) {
      alert('An error occurred: ' + error);
    });
}

function modifyDestination(id) {
  var latitude = prompt('Enter new latitude:');
  var longitude = prompt('Enter new longitude:');
  var deadline = prompt('Enter new deadline:');

  if (latitude !== null && longitude !== null && deadline !== null) {
    var data = {
      latitude: latitude,
      longitude: longitude,
      deadline: deadline
    };

    fetch(`http://127.0.0.1:5000/update_destination/${id}`, {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(data)
    })
      .then(function (response) {
        if (response.ok) {
          alert('Destination modified successfully!');
          loadDestinations();
        } else {
          throw new Error('Failed to modify destination.');
        }
      })
      .catch(function (error) {
        alert('An error occurred: ' + error);
      });
  }
}

document.getElementById('checking').addEventListener('click', async function (event) {
  // Prevent form submission if the button is inside a form (optional if not using form)
  event.preventDefault();
  var hubAddress = document.getElementById('hub-address').value;
  var numRoutes = document.getElementById('numRoutes').value
  if (hubAddress) {
    console.log('Hub Address:', hubAddress);
    const hubLatLong = await fetchCoordinatesFromAddress(hubAddress);
    //   if (hubLatLong) {
    //     console.log('Hub Latitude:', hubLatLong.lat);
    //     console.log('Hub Longitude:', hubLatLong.lon);
    // } else {
    //     console.log('Coordinates not found.');
    // }
    var data = {
      hubLatitude: hubLatLong.lat,
      hubLongitude: hubLatLong.lon,
      numRoutes : numRoutes
    }
    const response = await fetch('http://127.0.0.1:5000/create_hub', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(data)
    });
    if (response.status === 201) {
      alert("Hub Address commited successfuly")
    }
    else {
      alert('Failed to commit HubAddress')
    }
  } else {
    alert('Please enter a valid address.');
  }
});


function calculateOptimizedRoute() {
  fetch('http://127.0.0.1:5000/destinations')
    .then(function (response) {
      if (response.ok) {
        return response.json();
      } else {
        throw new Error('Failed to fetch destinations.');
      }
    })
    .then(function (data) {
      var destinations = data.destinations;
      var destinationsWithCoords = destinations.filter(function (dest) {
        return dest.latitude && dest.longitude;
      });

      var destinationCoords = destinationsWithCoords.map(function (dest) {
        return [parseFloat(dest.latitude), parseFloat(dest.longitude)];
      });

      var requestData = {
        destinations: destinationsWithCoords
      };

      // Fetch optimized route data
      return fetch('http://127.0.0.1:5000/plan_optimized_route', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(requestData)
      })
        .then(function (response) {
          if (response.ok) {
            return response.json();
          } else {
            throw new Error('Failed to calculate optimized route.');
          }
        })
        .then(function (data) {
          var optimizedRoutes = data.optimized_route;

          // Clear previous content
          document.getElementById('optimizedRouteSequence').innerHTML = '';

          // Loop through each optimized route and display it
          optimizedRoutes.forEach(function (optimizedRoute, routeIndex) {
            var optimizedRouteWithHub = ['Hub', ...optimizedRoute];
            var optimizedRouteSequence = optimizedRouteWithHub.join(' -> ');
            var routeElement = document.createElement('p');
            routeElement.textContent = `Route for cluster ${routeIndex + 1}: ${optimizedRouteSequence}`;
            document.getElementById('optimizedRouteSequence').appendChild(routeElement);
          });

          // Update the map iframe once after processing all routes
          const iframe = document.getElementById("mapContainer").querySelector("iframe");
          if (iframe) {
            iframe.src = "/static/backend/route_map.html";  // Always load the updated map with all routes
          }
        })
        .catch(function (error) {
          alert('An error occurred: ' + error);
        });
    })
    .catch(function (error) {
      alert('An error occurred: ' + error);
    });
}

function deleteDestination(id) {
  if (confirm("Are you sure you want to delete this destination?")) {
    fetch(`http://127.0.0.1:5000/delete_destination/${id}`, {
      method: 'DELETE'
    })
      .then(function (response) {
        if (response.ok) {
          alert('Destination deleted successfully!');
          loadDestinations(); 
        } else {
          throw new Error('Failed to delete destination.');
        }
      })
      .catch(function (error) {
        alert('An error occurred: ' + error);
      });
  }
}

function clearFields() {
  document.getElementById('address').value = '';
  document.getElementById('deadline').value = '';
}

var map = L.map('map').setView([13.04, 80.22], 12);

// Add OpenStreetMap tile layer to the map
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
  attribution: 'Map data © <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
}).addTo(map);

