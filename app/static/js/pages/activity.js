$(function() {
  $('#activity').jscroll({
    nextSelector: '.e-load-more a',
    loadingHtml: '<div class="e-load-more">' +
                 pageConfig.LOADING_TEXT +
                 '</div>',
    autoTrigger: false
  });
});
