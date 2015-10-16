$(function() {
  var VERTICAL_INSET_PX = 8;
  var currStep = $("meta[name=current-tutorial-step]").attr('content');

  function showPopup(id) {
    var target = $("[data-tutorial-target='" + id + "']");
    var popup = $("#tutorial-" + id);
    var topArrow = $('.e-top-arrow', popup);
    var top, left;

    if (!target.length) return;

    popup.addClass('m-active');

    top = Math.floor(target.offset().top + target.outerHeight() +
                     topArrow.outerHeight() - VERTICAL_INSET_PX);
    left = Math.floor(target.offset().left - topArrow.offset().left +
                      target.width() / 2);

    popup.css({top: top + 'px'});
    topArrow.css({left: left + 'px'});
  }

  function postTutorialStep(step) {
    $.post('/tutorial', {
      'step': step
    });
  }

  // Advance tutorial steps
  $("[data-tutorial-step]").click(function (evt) {
    var step = $(evt.target).data('tutorial-step');
    $(this).closest('.b-tutorial-box').removeClass('m-active');
    if (step) {
      postTutorialStep(step);
      showPopup(step);
    }
  });

  // For debugging only.
  window._resetTutorial = function() {
    postTutorialStep(1);
  }

  if (currStep) showPopup(currStep);
});
