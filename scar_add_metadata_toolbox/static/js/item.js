$(function() {
    // include the current tab in the URL on item pages
    //

    $('.bsk-nav-tabs').stickyTabs();

    // swap caret icons in collapsible information
    //

    // noinspection JSJQueryEfficiency
    $('.bsk-collapse').on('show.bs.collapse', function () {
        var trigger_icon = $('button[data-target="#' + this.id + '"] i').first();
        trigger_icon.toggleClass('fa-caret-right');
        trigger_icon.toggleClass('fa-caret-down');
    });
    // noinspection JSJQueryEfficiency
    $('.bsk-collapse').on('hide.bs.collapse', function () {
        var trigger_icon = $('button[data-target="#' + this.id + '"] i').first();
        trigger_icon.toggleClass('fa-caret-right');
        trigger_icon.toggleClass('fa-caret-down');
    });

    // Measure which items are viewed
    //

    gtag('event', 'view', {
      'event_category': 'item',
      'event_label': item_id
    });

    // Measure which tabs in items are viewed
    //

    $('#app-item-nav a[data-toggle="tab"]').on('shown.bs.tab', function (e) {
        var tab = e.target.hash.replace('#item-details-', '')
        gtag('event', 'tab', {
            'event_category': 'item',
            'event_label': tab
        });
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

var geographic_bounding_extent = {
    "type": "FeatureCollection",
    "name": "bounding_poly",
    "crs": {
        "type": "name",
        "properties": {
            "name": "urn:ogc:def:crs:EPSG::3031"
        }
    },
    "features": [
        {
            "type": "Feature",
            "properties": {
                "gid": 1,
                "label": "ADD data limit"
            },
            "geometry": {
                "type": "Polygon",
                "coordinates": [
                    [
                        [ -0.000005819109207, -3333134.027676715515554 ],
                        [ -232507.676298886770383, -3325014.680707213934511 ],
                        [ -463882.598564556566998, -3300696.196441804990172 ],
                        [ -692997.531439224374481, -3260297.052091349847615 ],
                        [ -918736.24995012988802, -3204014.068240646272898 ],
                        [ -1139998.977853273041546, -3132121.449904185254127 ],
                        [ -1355707.745328332995996, -3044969.450702776666731 ],
                        [ -1564811.640943090897053, -2942982.666416062042117 ],
                        [ -1766291.931537110125646, -2826657.966405434999615 ],
                        [ -1959167.025387293193489, -2696562.072916458826512 ],
                        [ -2142497.254424094222486, -2553328.800065048970282 ],
                        [ -2315389.452199890743941, -2397655.965958814136684 ],
                        [ -2477001.305306139867753, -2230301.992997379507869 ],
                        [ -2626545.457007425837219, -2052082.212955917464569 ],
                        [ -2763293.343295965809375, -1863864.894608139060438 ],
                        [ -2886578.742180570960045, -1666567.013848418835551 ],
                        [ -2995801.019590450450778, -1461149.78611955512315 ],
                        [ -3090428.055569021496922, -1248613.98350662435405 ],
                        [ -3169998.836708850227296, -1029995.059075984405354 ],
                        [ -3234125.702162629924715, -806358.102252019802108 ],
                        [ -3282496.232287866529077, -578792.649808516609482 ],
                        [ -3314874.770723965018988, -348407.377755039895419 ],
                        [ -3331103.572484511416405, -116324.700031127562397 ],
                        [ -3331103.572485930752009, 116324.699990476612584 ],
                        [ -3314874.770722748246044, 348407.377766617632005 ],
                        [ -3282496.232285845093429, 578792.649819981306791 ],
                        [ -3234125.702159813605249, 806358.102263315580785 ],
                        [ -3169998.836705251596868, 1029995.059087058994919 ],
                        [ -3090428.055564660578966, 1248613.983517418382689 ],
                        [ -2995801.01958534726873, 1461149.786130018532276 ],
                        [ -2886578.742174750193954, 1666567.013858501100913 ],
                        [ -2763293.343318711034954, 1863864.894574417034164 ],
                        [ -2626545.457032468169928, 2052082.21292386460118 ],
                        [ -2477001.305298350285739, 2230301.993006030563265 ],
                        [ -2315389.452191516757011, 2397655.965966900810599 ],
                        [ -2142497.254415175877512, 2553328.800072531681508 ],
                        [ -1959167.025377874495462, 2696562.072923301719129 ],
                        [ -1766291.931527236010879, 2826657.96641160454601 ],
                        [ -1564811.640932813985273, 2942982.666421526577324 ],
                        [ -1355707.7453176996205, 3044969.4507075115107 ],
                        [ -1139998.977891495916992, 3132121.449890273623168 ],
                        [ -918736.249989229603671, 3204014.068229434546083 ],
                        [ -692997.531427837326191, 3260297.052093770354986 ],
                        [ -463882.598553028190508, 3300696.196443425025791 ],
                        [ -232507.676287271577166, 3325014.680708026047796 ],
                        [ 0.000005823307071, 3333134.027676715515554 ],
                        [ 232507.676298889826285, 3325014.680707213934511 ],
                        [ 463882.598564561398234, 3300696.196441804524511 ],
                        [ 692997.531439226237126, 3260297.052091349381953 ],
                        [ 918736.249950131517835, 3204014.068240645807236 ],
                        [ 1139998.977853274671361, 3132121.449904184788465 ],
                        [ 1355707.745328336255625, 3044969.450702775269747 ],
                        [ 1564811.640943094389513, 2942982.666416060645133 ],
                        [ 1766291.931537112686783, 2826657.96640543313697 ],
                        [ 1959167.02538729691878, 2696562.072916456032544 ],
                        [ 2142497.254424097947776, 2553328.800065045710653 ],
                        [ 2315389.452199894469231, 2397655.965958810877055 ],
                        [ 2477001.305306143593043, 2230301.992997375782579 ],
                        [ 2626545.457007427234203, 2052082.212955916067585 ],
                        [ 2763293.343295966740698, 1863864.894608137197793 ],
                        [ 2886578.742180571891367, 1666567.013848417671397 ],
                        [ 2995801.019590451382101, 1461149.786119553493336 ],
                        [ 3090428.055569022428244, 1248613.983506622724235 ],
                        [ 3169998.836708850692958, 1029995.059075982775539 ],
                        [ 3234125.702162631321698, 806358.102252014563419 ],
                        [ 3282496.2322878674604, 578792.649808511836454 ],
                        [ 3314874.77072396595031, 348407.377755034365691 ],
                        [ 3331103.572484511416405, 116324.70003112575796 ],
                        [ 3331103.572485930286348, -116324.699990478446125 ],
                        [ 3314874.770722747780383, -348407.377766619436443 ],
                        [ 3282496.232285844627768, -578792.649819983053021 ],
                        [ 3234125.702159813605249, -806358.102263317327015 ],
                        [ 3169998.836705251131207, -1029995.059087060857564 ],
                        [ 3090428.055564659647644, -1248613.983517420012504 ],
                        [ 2995801.019585346337408, -1461149.786130020162091 ],
                        [ 2886578.742174749262631, -1666567.013858502265066 ],
                        [ 2763293.343318709172308, -1863864.894574420759454 ],
                        [ 2626545.457032464910299, -2052082.212923869024962 ],
                        [ 2477001.30529834702611, -2230301.993006034288555 ],
                        [ 2315389.452191513031721, -2397655.96596690453589 ],
                        [ 2142497.254415172617882, -2553328.800072534941137 ],
                        [ 1959167.025377869838849, -2696562.072923305444419 ],
                        [ 1766291.931527237640694, -2826657.966411604080349 ],
                        [ 1564811.640932811424136, -2942982.666421527974308 ],
                        [ 1355707.745317697525024, -3044969.450707511976361 ],
                        [ 1139998.977891490561888, -3132121.449890275485814 ],
                        [ 918736.249989224597812, -3204014.068229435943067 ],
                        [ 692997.531427832553163, -3260297.052093770820647 ],
                        [ 463882.598553023708519, -3300696.196443425957114 ],
                        [ 232507.676287265872816, -3325014.680708026513457 ],
                        [ -0.000005829470669, -3333134.027676715515554 ]
                    ]
                ]
            }
        }
    ]
};
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
