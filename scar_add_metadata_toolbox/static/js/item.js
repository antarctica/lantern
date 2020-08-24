// Include current tab in the URL on item pages
//

$(function() {
    $('.bsk-nav-tabs').stickyTabs();
});

// Swap caret icons in collapsible information
//

$(function() {
    $('.app-collapsible-section').on('show.bs.collapse', function () {
        var trigger_icon = $('button[data-target="#' + this.id + '"] i').first();
        trigger_icon.toggleClass('fa-caret-right');
        trigger_icon.toggleClass('fa-caret-down');
    });
    $('.app-collapsible-section').on('hide.bs.collapse', function () {
        var trigger_icon = $('button[data-target="#' + this.id + '"] i').first();
        trigger_icon.toggleClass('fa-caret-right');
        trigger_icon.toggleClass('fa-caret-down');
    });
});

// Metrics
//

$(function() {
    gtag('event', 'view', {
      'event_category': 'item',
      'event_label': item_id
    });
    $('#app-item-nav a[data-toggle="tab"]').on('shown.bs.tab', function (e) {
        var tab = e.target.hash.replace('#item-details-', '')
        gtag('event', 'tab', {
            'event_category': 'item',
            'event_label': tab
        });
    });
});


// Scroll WMS instructions box into view
//

$(function() {
    $('.app-wms-info').on('shown.bs.collapse', function () {
        document.getElementById(this.id).scrollIntoView()
        document.getElementById(this.id).classList.add('app-highlight');
    });
    // $('.app-wms-info-trigger').click(function () {
    //     var instructions_box = $($(this).data('target'))[0];
    //     instructions_box.scrollIntoView();
    // })
});

// Item contact form
//

function itemContactFormSubmit(e, form) {
    e.preventDefault();
    $(form).find('#contact-form-control').toggleClass('bsk-disabled');
    $(form).find('#contact-form-control i').toggleClass('fa-envelope');
    $(form).find('#contact-form-control i').toggleClass('fa-spin');
    $(form).find('#contact-form-control i').toggleClass('fa-circle-notch');
    $(form).find('#contact-form-control span').text('Sending message');

    var md = window.markdownit();
    md.set({gfm: true});

    fetch('https://prod-66.westeurope.logic.azure.com:443/workflows/21919e9ce6964d1c90d520eff13214c7/triggers/manual/paths/invoke?api-version=2016-06-01&sp=%2Ftriggers%2Fmanual%2Frun&sv=1.0&sig=WUJcFcM-hXnylyQna0ZpvUuIflk5tCW_scCASG6SYFE', {
        method: 'post',
        headers: new Headers({'content-type': 'application/json;charset=UTF-8'}),
        body: JSON.stringify({
            'service-id': 'add-data-catalogue',
            'type': 'message',
            'subject': form['message-subject'].value,
            'content': md.render(form['message-content'].value),
            'sender-name': form['message-sender-name'].value,
            'sender-email': form['message-sender-email'].value
        })
    }).then(function (response) {
        if (response.ok) {
            $(form).find('#contact-form-control').toggleClass('bsk-btn-primary');
            $(form).find('#contact-form-control').toggleClass('bsk-btn-success');
            $(form).find('#contact-form-control i').toggleClass('fa-spin');
            $(form).find('#contact-form-control i').toggleClass('fa-circle-notch');
            $(form).find('#contact-form-control i').toggleClass('fa-check');
            $(form).find('#contact-form-control span').text('Message sent');
            $(form).find('#contact-form-result').toggleClass('bsk-hidden');
            $(form).find('#contact-form-result').toggleClass('bsk-in');
            $(form).find('#contact-form-result').toggleClass('bsk-alert-success');
            $(form).find('#contact-form-result').text('Message sent successfully, you should hear from us soon.');

            gtag('event', 'contact', {
              'event_category': 'item',
              'event_label': item_id
            });
        } else {
            $(form).find('#contact-form-control').toggleClass('bsk-btn-primary');
            $(form).find('#contact-form-control').toggleClass('bsk-btn-danger');
            $(form).find('#contact-form-control i').toggleClass('fa-spin');
            $(form).find('#contact-form-control i').toggleClass('fa-circle-notch');
            $(form).find('#contact-form-control i').toggleClass('fa-times-circle');
            $(form).find('#contact-form-control span').text('Message failed to send');
            $(form).find('#contact-form-result').toggleClass('bsk-hidden');
            $(form).find('#contact-form-result').toggleClass('bsk-in');
            $(form).find('#contact-form-result').toggleClass('bsk-alert-danger');
            $(form).find('#contact-form-result').text('Sorry, something went wrong sending your message. Please try again later or use an alternative contact method.');
        }
    }).catch(function (err) {
        $(form).find('#contact-form-control').toggleClass('bsk-btn-primary');
        $(form).find('#contact-form-control').toggleClass('bsk-btn-danger');
        $(form).find('#contact-form-control i').toggleClass('fa-spin');
        $(form).find('#contact-form-control i').toggleClass('fa-circle-notch');
        $(form).find('#contact-form-control i').toggleClass('fa-times-circle');
        $(form).find('#contact-form-control span').text('Message failed to send');
        $(form).find('#contact-form-result').toggleClass('bsk-hidden');
        $(form).find('#contact-form-result').toggleClass('bsk-in');
        $(form).find('#contact-form-result').toggleClass('bsk-alert-danger');
        $(form).find('#contact-form-result').text('Sorry, something went wrong sending your message. Please try again later or use an alternative contact method.');
    });
}

// Item map
//

var epsg_3031 = new L.Proj.CRS(
  'EPSG:3031',
  '+proj=stere +lat_0=-90 +lat_ts=-71 +lon_0=0 +k=1 +x_0=0 +y_0=0 +ellps=WGS84 +datum=WGS84 +units=m +no_defs ',
  {
    origin: [-4194304, 4194304],
    resolutions: [
      16384,
      8192,
      4096,
      2048,
      1024,
      512,
    ]
  }
);

var antarctica = L.tileLayer.wms('https://maps.bas.ac.uk/antarctic/wms?tiled=true', {
  attribution: 'Map data <a href="https://www.add.scar.org">SCAR Antarctic Digital Database</a>',
  layers: 'add:antarctic_rema_z5_hillshade_and_bathymetry',
  format: 'image/png',
  transparent: true,
  crs: epsg_3031
});
var sub_antarctica = L.tileLayer.wms('https://maps.bas.ac.uk/antarctic/wms?tiled=true', {
  continuousWorld: true,
  layers: 'add:sub_antarctic_coastline',
  format: 'image/png',
  transparent: true,
  crs: epsg_3031
});

var map = L.map('item-map', {
  attribution: false,
  crs: epsg_3031,
  layers: [
    antarctica,
    sub_antarctica
  ],
  center: [-90, 0],
  zoom: 0,
  maxZoom: 5
});
map.attributionControl.setPrefix(false);
L.control.scale().addTo(map);

function geographic_bounding_extent_style(feature) {
  return {
    weight: 2,
    opacity: 1,
    color: '#CC0033',
    fill: '#CC0033',
  };
}
L.Proj.geoJson(geographic_bounding_extent, {style: geographic_bounding_extent_style()}).addTo(map);

$(function() {
  // Ensure map is corrected when viewed in a tab
  //

  $('#app-item-nav a[data-toggle="tab"]').on('shown.bs.tab', function (e) {
    if (e.target.hash === '#item-details-extent') {
      map.invalidateSize();
    }
  })
});
