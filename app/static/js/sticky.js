$(function() {
    // set flag to determine whether to show sticky on login
    function setStickyFlag(truefalse) {
        $.post('/sticky', {
          'show': truefalse
      });
    }

    $(".js-sticky-on").click(function (evt) {
        $($(this).attr('data-target')).removeClass('m-hide');
        setStickyFlag(true);
    });
    $(".js-sticky-off").click(function (evt) {
        $($(this).attr('data-target')).addClass('m-hide');
        setStickyFlag(false);
    });
});