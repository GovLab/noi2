$(function () {
  $('.js-scroll-btn').click(function(e) {
    var x;
    if ($(this).hasClass('js-left')) { x = -50; }
    else if ($(this).hasClass('js-right')) { x = 50; }

    // $($(this).attr('data-target')).scrollLeft(
    //   $($(this).attr('data-target')).scrollLeft() + x
    // );


    $($(this).attr('data-target')).animate({
        scrollLeft: $($(this).attr('data-target')).scrollLeft() + x
    }, 2000, 'swing' );
  });
});