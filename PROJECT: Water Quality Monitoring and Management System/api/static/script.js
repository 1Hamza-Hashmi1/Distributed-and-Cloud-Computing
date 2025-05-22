let map;
let markers = {};
let currentStation = null;
let socket = null;
let connectionLines = [];

document.addEventListener('DOMContentLoaded', async () => {
    initMap();
    await loadStations();
    connectWebSocket();
    setupNeighborControls();
});

function initMap() {
    try {
        const mapContainer = document.getElementById('map');
        if (!mapContainer) {
            throw new Error('Map container not found');
        }

        mapContainer.style.height = '500px';
        mapContainer.style.width = '100%';

        if (map) {
            map.remove();
        }

        map = L.map('map').setView([43.6532, -79.3832], 12);
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        }).addTo(map);

        console.log('Map initialized successfully');
    } catch (error) {
        console.error('Map initialization failed:', error);
    }
}

async function loadStations() {
    try {
        const response = await fetch('/api/stations');
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        populateStationList(data.stations);
        addMarkersToMap(data.stations);
    } catch (error) {
        console.error('Error loading stations:', error);
    }
}

function populateStationList(stations) {
    const list = document.getElementById('station-list');
    list.innerHTML = '';
    stations.forEach(station => {
        const li = document.createElement('li');
        li.textContent = station.name;
        li.dataset.stationId = station.id;
        li.addEventListener('click', () => selectStation(station.id));
        list.appendChild(li);
    });
}

function addMarkersToMap(stations) {
    stations.forEach(station => {
        const neighbors = Array.isArray(station.neighbors) ? station.neighbors : [];

        const marker = L.marker(station.coordinates, {
            title: station.name
        }).addTo(map);

        marker.bindPopup(`
            <b>${station.name}</b><br>
            Status: ${station.status || 'unknown'}<br>
            Neighbors: ${neighbors.join(', ') || 'None'}
        `);

        markers[station.id] = marker;
        updateMarkerStyle(station.id, station.status);
    });
}

async function selectStation(stationId) {
    currentStation = stationId;
    document.querySelectorAll('#station-list li').forEach(li => {
        li.classList.toggle('active', li.dataset.stationId === stationId);
    });
    await highlightNeighbors(stationId);
    await drawConnections(stationId);
    await loadStationDetails(stationId);
}

async function highlightNeighbors(stationId) {
    try {
        // Reset all markers first
        Object.values(markers).forEach(marker => {
            marker._icon.classList.remove('neighbor-highlight');
        });

        const response = await fetch(`/api/stations/${stationId}/neighbors`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();

        if (data && Array.isArray(data.neighbors)) {
            data.neighbors.forEach(neighborId => {
                if (markers[neighborId]) {
                    markers[neighborId]._icon.classList.add('neighbor-highlight');
                }
            });
        }
    } catch (error) {
        console.error('Error loading neighbors:', error);
    }
}

async function drawConnections(stationId) {
    // Remove existing lines
    connectionLines.forEach(line => map.removeLayer(line));
    connectionLines = [];

    try {
        const response = await fetch(`/api/stations/${stationId}/neighbors`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();

        const mainStation = markers[stationId];
        if (!mainStation) return;

        if (data && Array.isArray(data.neighbors)) {
            data.neighbors.forEach(neighborId => {
                if (markers[neighborId]) {
                    const line = L.polyline(
                        [mainStation.getLatLng(), markers[neighborId].getLatLng()],
                        {
                            color: '#3498db',
                            weight: 3,
                            dashArray: '5,5',
                            opacity: 0.7
                        }
                    ).addTo(map);

                    // Add midpoint marker with connection info
                    const midpoint = L.latLngBounds(
                        mainStation.getLatLng(),
                        markers[neighborId].getLatLng()
                    ).getCenter();

                    const connectionMarker = L.marker(midpoint, {
                        icon: L.divIcon({
                            className: 'connection-label',
                            html: `${stationId} ↔ ${neighborId}`,
                            iconSize: [100, 20]
                        })
                    }).addTo(map);

                    connectionLines.push(line);
                    connectionLines.push(connectionMarker);
                }
            });
        }
    } catch (error) {
        console.error('Error drawing connections:', error);
    }
}

async function loadStationDetails(stationId) {
    try {
        const response = await fetch(`/api/stations/${stationId}`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const station = await response.json();

        // Update metrics display
        const phValue = document.getElementById('ph-value').querySelector('.value');
        phValue.textContent = station.metrics.ph.toFixed(2);
        phValue.className = 'value ' + getStatusClass(station.metrics.ph, 6, 8);

        const turbidityValue = document.getElementById('turbidity-value').querySelector('.value');
        turbidityValue.textContent = station.metrics.turbidity.toFixed(2);
        turbidityValue.className = 'value ' + getStatusClass(station.metrics.turbidity, null, 7);

        const pollutantsValue = document.getElementById('pollutants-value').querySelector('.value');
        pollutantsValue.textContent = station.metrics.pollutants.toFixed(2);
        pollutantsValue.className = 'value ' + getStatusClass(station.metrics.pollutants, null, 70);

        const statusValue = document.getElementById('status-value').querySelector('.value');
        statusValue.textContent = station.status;
        statusValue.className = 'value ' + station.status;
    } catch (error) {
        console.error('Error loading station details:', error);
    }
}

function getStatusClass(value, min, max) {
    if (min !== null && value < min) return 'critical';
    if (max !== null && value > max) return 'critical';
    if (max !== null && value > max * 0.8) return 'warning';
    return 'normal';
}

function connectWebSocket() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws`;

    socket = new WebSocket(wsUrl);

    socket.onopen = () => {
        console.log('WebSocket connected');
        document.getElementById('connection-status').textContent = 'Connected';
    };

    socket.onmessage = (event) => {
        const message = JSON.parse(event.data);
        console.log('WebSocket message:', message);

        if (message.type === 'sensor_update') {
            updateStationMetrics(message.data);
        }
        else if (message.type === 'alert') {
            addAlert(message.data.station_id, message.data.message, new Date(message.data.timestamp * 1000));
        }
        else if (message.type === 'neighbor_update') {
            if (currentStation === message.station_id || currentStation === message.neighbour_id) {
                highlightNeighbors(currentStation);
                drawConnections(currentStation);
            }
        }
        else if (message.type === 'sensor_status') {  // Add this new case
            updateSensorStatus(message.data);
        }
    };

    socket.onclose = () => {
        console.log('WebSocket disconnected');
        document.getElementById('connection-status').textContent = 'Disconnected';
        setTimeout(connectWebSocket, 5000);
    };
}

function updateStationMetrics(data) {
    if (markers[data.station_id]) {
        updateMarkerStyle(data.station_id, data.status);
    }

    if (currentStation === data.station_id) {
        const phValue = document.getElementById('ph-value').querySelector('.value');
        phValue.textContent = data.metrics.ph.toFixed(2);
        phValue.className = 'value ' + getStatusClass(data.metrics.ph, 6, 8);

        const turbidityValue = document.getElementById('turbidity-value').querySelector('.value');
        turbidityValue.textContent = data.metrics.turbidity.toFixed(2);
        turbidityValue.className = 'value ' + getStatusClass(data.metrics.turbidity, null, 7);

        const pollutantsValue = document.getElementById('pollutants-value').querySelector('.value');
        pollutantsValue.textContent = data.metrics.pollutants.toFixed(2);
        pollutantsValue.className = 'value ' + getStatusClass(data.metrics.pollutants, null, 70);

        const statusValue = document.getElementById('status-value').querySelector('.value');
        statusValue.textContent = data.status;
        statusValue.className = 'value ' + data.status;
    }
}

function updateMarkerStyle(stationId, status) {
    const marker = markers[stationId];
    if (!marker) return;

    marker._icon.classList.remove('normal-marker', 'warning-marker', 'critical-marker', 'neighbor-highlight');
    marker._icon.classList.add(`${status}-marker`);
}

function addAlert(stationId, message, timestamp) {
    const alertsContainer = document.getElementById('alerts-container');
    const alertElement = document.createElement('div');
    alertElement.className = 'alert';
    alertElement.innerHTML = `
        <span class="time">${timestamp.toLocaleTimeString()}</span>
        <span class="station">${stationId}</span>
        <span class="message">${message}</span>
    `;
    alertsContainer.prepend(alertElement);
    setTimeout(() => alertElement.remove(), 30000);
}

function setupNeighborControls() {
    document.getElementById('toggle-neighbors').addEventListener('click', () => {
        document.querySelectorAll('.neighbor-highlight').forEach(el => {
            el.classList.toggle('hidden');
        });
    });

    document.getElementById('toggle-connections').addEventListener('click', () => {
        connectionLines.forEach(line => {
            line.setStyle({
                opacity: line.options.opacity === 0 ? 0.7 : 0
            });
        });
    });

    document.getElementById('add-neighbor').addEventListener('click', async () => {
        if (!currentStation) {
            alert('Please select a station first');
            return;
        }

        const neighborId = prompt('Enter neighbor station ID:');
        if (!neighborId) return;

        if (neighborId === currentStation) {
            alert('Cannot add self as neighbor');
            return;
        }

        try {
            const response = await fetch(`/api/stations/${currentStation}/neighbors`, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({neighbor_id: neighborId})
            });

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.detail || errorData.message || 'Failed to add neighbor');
            }

            const result = await response.json();
            console.log('Neighbor added:', result);

            // Refresh the display
            await highlightNeighbors(currentStation);
            await drawConnections(currentStation);

            // Show success message
            addAlert(currentStation, `Successfully added ${neighborId} as neighbor`, new Date());

        } catch (error) {
            console.error('Error adding neighbor:', error);
            alert(`Error: ${error.message}`);
        }
    });
}