$(function () {
  $('.js-scroll-btn').click(function(e) {
    var x;
    if ($(this).hasClass('js-left')) { x = -50; }
    else if ($(this).hasClass('js-right')) { x = 50; }

    console.log('potat');
    console.log('biyat');

    $($(this).attr('data-target')).scrollLeft(
      $($(this).attr('data-target')).scrollLeft() + x
    );
  });
});