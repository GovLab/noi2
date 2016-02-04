$(function() {
  $('#activity').jscroll({
    nextSelector: '.e-load-more a',
    loadingHtml: '<div class="e-load-more">' +
                 pageConfig.LOADING_TEXT +
                 '</div>',
    autoTrigger: false,
    callback: function() {
      $('time', this).timeago();
    }
  });

  var lang = $('html').attr('lang');

  // https://github.com/rmm5t/jquery-timeago/tree/master/locales
  if (lang == 'es') {
    // Spanish
    jQuery.timeago.settings.strings = {
       prefixAgo: "hace",
       prefixFromNow: "dentro de",
       suffixAgo: "",
       suffixFromNow: "",
       seconds: "menos de un minuto",
       minute: "un minuto",
       minutes: "unos %d minutos",
       hour: "una hora",
       hours: "%d horas",
       day: "un día",
       days: "%d días",
       month: "un mes",
       months: "%d meses",
       year: "un año",
       years: "%d años"
    };
  } else {
    $.extend($.timeago.settings.strings, {
      inPast: 'just now',
      seconds: 'seconds',
      minute: "1 min",
      minutes: "%d mins",
      hour: "an hour",
      hours: "%d hours",
      month: "a month",
      year: "a year",
    });
  }
  $('time').timeago();

  var $showMoreBlogItems = $('.e-feed-item.m-show-more-blog-items');
  var $showLessBlogItems = $('.e-feed-item.m-show-less-blog-items');
  var $moreBlogItems = $('.e-more-blog-items');

  $showMoreBlogItems.click(function() {
    $showMoreBlogItems.slideUp('fast');
    $moreBlogItems.slideDown();
  });

  $showLessBlogItems.click(function() {
    $moreBlogItems.slideUp('fast');
    $showMoreBlogItems.slideDown();
  });
});
