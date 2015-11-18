/*jslint browser:true*/
/*globals $*/

try{Typekit.load();}catch(e){}

var csrftoken = $('meta[name=csrf-token]').attr('content');
var globalConfig = $('meta[name=global-config-json]').attr('content');
var pageConfig = $('meta[name=page-config-json]').attr('content');

['pageConfig', 'globalConfig'].forEach(function(key) {
  if (window[key]) {
    try {
      window[key] = JSON.parse(window[key]);
    } catch (e) {
      // This is a pretty fatal error!
      window.alert("Unable to parse " + key + ": " + e);
    }
  } else {
    window[key] = {};
  }
});

$.ajaxSetup({
  beforeSend: function(xhr, settings) {
    if (!/^(GET|HEAD|OPTIONS|TRACE)$/i.test(settings.type) &&
        !this.crossDomain) {
      xhr.setRequestHeader("X-CSRFToken", csrftoken);
    }
  }
});

$(document).ready(function () {
  // Keep track of mailto: links as connections
  $("a[href^=mailto]").click(function (evt) {
    var connectTo = $(this).data('connect-to');
    if (connectTo) {
      $.post('/email', {
        'emails': connectTo.split(',')
      });
    }
  });

  $('form[data-submit-on-change]').change(function() {
    this.submit();
  });

  // Ensure the name of our active tab on our horizontally-scrollabar
  // tab bars is visible.
  $('.b-contextual-nav').each(function() {
    var active = $('li.active', this);
    var offset = active.offset();
    if (!offset) return;
    if (offset.left > window.innerWidth - 100) {
      $(this).scrollLeft(offset.left);
    }
  });
});
