/**
 * Leaflet Interactive Map Controller with Route Animation & Timeline Sync
 * (Polarsteps-inspired experience)
 */

document.addEventListener('DOMContentLoaded', () => {
  const mapElement = document.getElementById('map');
  if (!mapElement) return;

  const tripSlug = mapElement.dataset.tripSlug;
  if (!tripSlug) return;

  // 1. Initialize Map
  const map = L.map('map', {
    zoomControl: true,
    scrollWheelZoom: true,
  }).setView([20, 0], 2);

  // 2. Add modern clean tile layer (CartoDB Positron / OSM style)
  L.tileLayer('https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png', {
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
    subdomains: 'abcd',
    maxZoom: 19
  }).addTo(map);

  const markers = {};
  let routePolyline = null;
  let activeStepId = null;

  // 3. Fetch GeoJSON for the current trip
  fetch(`/api/trips/${tripSlug}/geojson`)
    .then(response => {
      if (!response.ok) throw new Error('Erreur lors du chargement des données géographiques');
      return response.json();
    })
    .then(data => {
      const features = data.features || [];
      const latlngs = [];
      const bounds = L.latLngBounds([]);

      // Process Route LineString
      const routeFeature = features.find(f => f.geometry.type === 'LineString');
      const pointFeatures = features.filter(f => f.geometry.type === 'Point');

      if (pointFeatures.length === 0) {
        // No steps yet
        return;
      }

      // Add Custom Numbered Markers
      pointFeatures.forEach(feature => {
        const coords = feature.geometry.coordinates;
        const latlng = [coords[1], coords[0]];
        latlngs.push(latlng);
        bounds.extend(latlng);

        const props = feature.properties;
        const stepNum = props.step_number;
        const entryId = props.id;

        // Custom DivIcon for Polarsteps-like Pin
        const iconHtml = `
          <div class="polar-pin" id="marker-pin-${entryId}">
            <span>${stepNum}</span>
          </div>
        `;

        const customIcon = L.divIcon({
          className: 'custom-polar-marker',
          html: iconHtml,
          iconSize: [34, 34],
          iconAnchor: [17, 34],
          popupAnchor: [0, -32]
        });

        const marker = L.marker(latlng, { icon: customIcon }).addTo(map);
        markers[entryId] = marker;

        // Rich Popup Content
        let popupContent = `
          <div class="map-popup-card">
            ${props.thumbnail_url ? `<img src="${props.thumbnail_url}" class="map-popup-thumb" alt="${props.title}" />` : ''}
            <div class="map-popup-body">
              <div class="map-popup-meta">📍 Étape ${stepNum} • ${props.date}</div>
              <div class="map-popup-title">${props.title}</div>
              <div class="map-popup-meta" style="color: #64748B;">${props.location_name}</div>
            </div>
          </div>
        `;
        marker.bindPopup(popupContent);

        // Click on Marker -> Scroll to Timeline card
        marker.on('click', () => {
          highlightStep(entryId, false);
          const targetCard = document.getElementById(`entry-${entryId}`);
          if (targetCard) {
            targetCard.scrollIntoView({ behavior: 'smooth', block: 'center' });
          }
        });
      });

      // Fit map bounds to encompass all points
      if (latlngs.length > 0) {
        map.fitBounds(bounds, { padding: [50, 50], maxZoom: 14 });
      }

      // Draw Animated Route Polyline
      if (latlngs.length >= 2) {
        // 1. Background dashed shadow line
        L.polyline(latlngs, {
          color: '#CBD5E1',
          weight: 5,
          opacity: 0.8,
          lineCap: 'round',
          lineJoin: 'round'
        }).addTo(map);

        // 2. Foreground dynamic coral line with animated effect
        routePolyline = L.polyline(latlngs, {
          color: '#FF5A5F',
          weight: 4,
          opacity: 0.9,
          dashArray: '8, 8',
          lineCap: 'round',
          lineJoin: 'round'
        }).addTo(map);

        // Animate stroke dashoffset if supported
        animateRoute(routePolyline);
      }

      // Setup Timeline Hover & Click Listeners
      setupTimelineInteractions();
    })
    .catch(err => {
      console.error('Map loading error:', err);
    });

  // Animated Route Dash
  function animateRoute(polyline) {
    let offset = 0;
    const path = polyline._path;
    if (path) {
      function step() {
        offset = (offset - 1) % 16;
        polyline.setStyle({ dashOffset: `${offset}px` });
        requestAnimationFrame(step);
      }
      step();
    }
  }

  // Highlight step on both map and timeline
  function highlightStep(entryId, panMap = true) {
    if (activeStepId === entryId) return;
    activeStepId = entryId;

    // Update active class on cards
    document.querySelectorAll('.step-card').forEach(card => {
      card.classList.remove('active-step');
    });
    const activeCard = document.getElementById(`entry-${entryId}`);
    if (activeCard) {
      activeCard.classList.add('active-step');
    }

    // Update active class on marker pins
    document.querySelectorAll('.polar-pin').forEach(pin => {
      pin.classList.remove('active');
    });
    const activePin = document.getElementById(`marker-pin-${entryId}`);
    if (activePin) {
      activePin.classList.add('active');
    }

    // Pan map to marker if requested
    const marker = markers[entryId];
    if (marker) {
      if (panMap) {
        map.panTo(marker.getLatLng(), { animate: true, duration: 0.6 });
        marker.openPopup();
      }
    }
  }

  // Setup interactions with timeline DOM elements (Hover, Click, and Scroll Observation)
  function setupTimelineInteractions() {
    const stepCards = document.querySelectorAll('.step-card');
    if (stepCards.length === 0) return;

    stepCards.forEach(card => {
      const entryId = card.dataset.entryId;
      if (!entryId) return;

      // Click or Hover on timeline card
      card.addEventListener('mouseenter', () => {
        highlightStep(entryId, true);
      });

      card.addEventListener('click', (e) => {
        // Prevent if clicking an action link
        if (e.target.closest('a') || e.target.closest('button')) return;
        highlightStep(entryId, true);
      });
    });

    // IntersectionObserver for auto-highlighting when scrolling the timeline
    if ('IntersectionObserver' in window) {
      const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
          if (entry.isIntersecting) {
            const entryId = entry.target.dataset.entryId;
            if (entryId) {
              highlightStep(entryId, true);
            }
          }
        });
      }, {
        root: null,
        rootMargin: '-20% 0px -60% 0px', // Trigger when card is in the upper-middle viewport
        threshold: 0.1
      });

      stepCards.forEach(card => observer.observe(card));
    }
  }

  // Lightbox Modal Setup
  const lightboxModal = document.getElementById('lightbox-modal');
  const lightboxImg = document.getElementById('lightbox-img');
  const lightboxCaption = document.getElementById('lightbox-caption');
  const lightboxClose = document.getElementById('lightbox-close');

  if (lightboxModal && lightboxImg) {
    document.querySelectorAll('.media-photo-wrapper img').forEach(img => {
      img.addEventListener('click', (e) => {
        e.stopPropagation();
        const fullSrc = img.dataset.fullSrc || img.src;
        const caption = img.dataset.caption || '';
        lightboxImg.src = fullSrc;
        lightboxCaption.textContent = caption;
        lightboxModal.classList.add('active');
      });
    });

    const closeModal = () => {
      lightboxModal.classList.remove('active');
    };

    if (lightboxClose) lightboxClose.addEventListener('click', closeModal);
    lightboxModal.addEventListener('click', (e) => {
      if (e.target === lightboxModal) closeModal();
    });
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && lightboxModal.classList.contains('active')) {
        closeModal();
      }
    });
  }
});
