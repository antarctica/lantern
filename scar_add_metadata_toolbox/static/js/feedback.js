function feedbackFormSubmit(e, form) {
    e.preventDefault();
    $(form).find('#contact-form-control').toggleClass('bsk-disabled');
    $(form).find('#contact-form-control i').toggleClass('fa-envelope');
    $(form).find('#contact-form-control i').toggleClass('fa-spin');
    $(form).find('#contact-form-control i').toggleClass('fa-circle-notch');
    $(form).find('#contact-form-control span').text('Sending message');

    var md = window.markdownit();
    md.set({gfm: true});

    var payload = {
        'service-id': 'add-data-catalogue',
        'type': 'feedback',
        'subject': 'feedback-message',
        'content': md.render(form['feedback-content'].value),
    };
    if (!(form['feedback-sender-name'].value === '')) {
        payload['sender-name'] = form['feedback-sender-name'].value
    }
    if (!(form['feedback-sender-email'].value === '')) {
        payload['sender-email'] = form['feedback-sender-email'].value
    }

    fetch('https://prod-66.westeurope.logic.azure.com:443/workflows/21919e9ce6964d1c90d520eff13214c7/triggers/manual/paths/invoke?api-version=2016-06-01&sp=%2Ftriggers%2Fmanual%2Frun&sv=1.0&sig=WUJcFcM-hXnylyQna0ZpvUuIflk5tCW_scCASG6SYFE', {
        method: 'post',
        headers: new Headers({'content-type': 'application/json;charset=UTF-8'}),
        body: JSON.stringify(payload)
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
            $(form).find('#contact-form-result').text('Feedback sent successfully, thank you.');

            gtag('event', 'feedback', {
              'event_category': 'app'
            });
        } else {
            $(form).find('#contact-form-control').toggleClass('bsk-btn-primary');
            $(form).find('#contact-form-control').toggleClass('bsk-btn-danger');
            $(form).find('#contact-form-control i').toggleClass('fa-spin');
            $(form).find('#contact-form-control i').toggleClass('fa-circle-notch');
            $(form).find('#contact-form-control i').toggleClass('fa-times-circle');
            $(form).find('#contact-form-control span').text('Feedback failed to send');
            $(form).find('#contact-form-result').toggleClass('bsk-hidden');
            $(form).find('#contact-form-result').toggleClass('bsk-in');
            $(form).find('#contact-form-result').toggleClass('bsk-alert-danger');
            $(form).find('#contact-form-result').html('Sorry, something went wrong sending your feedback. Please try again later or email <a href="mailto:servicedesk@bas.ac.uk" class="bsk-alert-link">servicedesk@bas.ac.uk</a> if this problem persists.');
        }
    }).catch(function (err) {
        $(form).find('#contact-form-control').toggleClass('bsk-btn-primary');
        $(form).find('#contact-form-control').toggleClass('bsk-btn-danger');
        $(form).find('#contact-form-control i').toggleClass('fa-spin');
        $(form).find('#contact-form-control i').toggleClass('fa-circle-notch');
        $(form).find('#contact-form-control i').toggleClass('fa-times-circle');
        $(form).find('#contact-form-control span').text('Feedback failed to send');
        $(form).find('#contact-form-result').toggleClass('bsk-hidden');
        $(form).find('#contact-form-result').toggleClass('bsk-in');
        $(form).find('#contact-form-result').toggleClass('bsk-alert-danger');
        $(form).find('#contact-form-result').html('Sorry, something went wrong sending your feedback. Please try again later or email <a href="mailto:servicedesk@bas.ac.uk" class="bsk-alert-link">servicedesk@bas.ac.uk</a> if this problem persists.');
    });
}
