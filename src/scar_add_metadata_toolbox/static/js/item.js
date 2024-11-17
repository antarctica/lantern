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


// Scroll instruction boxes into view
//

$(function() {
    // ArcGIS feature layers
    $('.app-fl-info').on('shown.bs.collapse', function () {
        document.getElementById(this.id).scrollIntoView()
        document.getElementById(this.id).classList.add('app-highlight');
    });

    // ArcGIS tile layers
    $('.app-tl-info').on('shown.bs.collapse', function () {
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
