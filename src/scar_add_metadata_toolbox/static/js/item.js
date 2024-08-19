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

function itemMap() {
    require([
        "esri/config",
        "esri/geometry/Polygon",
        "esri/Map",
        "esri/views/MapView",
        "esri/Basemap",
        "esri/layers/TileLayer",
        "esri/Graphic",
        "esri/layers/GraphicsLayer",
        "esri/widgets/ScaleBar"
    ], function (
        esriConfig,
        Polygon,
        Map,
        MapView,
        Basemap,
        TileLayer,
        Graphic,
        GraphicsLayer,
        ScaleBar
    ) {
        const polygon = new Polygon({
          rings: geographic_bounding_extent.features[0].geometry.coordinates,
          spatialReference: { wkid: 4326 }
        });

        const simpleFillSymbol = {
            type: "simple-fill",
            color: [204, 0, 51, 0.2], // #CC0033 @ 80% opacity
            outline: {
                color: [204, 0, 51, 1], // #CC0033
                width: 1
            }
        };

        const graphicsLayer = new GraphicsLayer();

        const polygonGraphic = new Graphic({
            geometry: polygon,
            symbol: simpleFillSymbol
        });

        const basemapLayer = new TileLayer({
            portalItem: {
                id: "35d47151a80747a79767901444e1fe80"
            }
        });

        const basemap = new Basemap({
            baseLayers: [basemapLayer]
        });

        const map = new Map({
            basemap: basemap
        });

        const view = new MapView({
            map: map,
            container: "item-map",
            extent: polygon.extent
        });

        const ESRIscaleBar = new ScaleBar({
            unit: "dual",
            view: view
        });

        graphicsLayer.add(polygonGraphic);
        map.add(graphicsLayer);
        view.ui.add(ESRIscaleBar, {position: "bottom-left"});
    });
}

$(function() {
    $('#app-item-nav a[data-toggle="tab"]').on('shown.bs.tab', function (e) {
        itemMap();
    })
});
