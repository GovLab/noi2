$(function() {
  $('[data-set-height-to]').each(function() {
    var target = $($(this).data('set-height-to'));
    $(this).height(target.height());
  });
});
