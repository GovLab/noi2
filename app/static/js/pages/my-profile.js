function upload(canvas, cb) {
  canvas.toBlob(function(blob) {
    var fd = new FormData();

    fd.append('picture', blob, 'picture.jpg');

    $.ajax({
      url: pageConfig.UPLOAD_PICTURE_URL,
      type: 'POST',
      data: fd,
      processData: false,
      contentType: false,
      complete: cb,
      success: function(data, textStatus) {
        alert(pageConfig.UPLOAD_PICTURE_SUCCESS);
      },
      error: function() {
        alert(pageConfig.UPLOAD_PICTURE_ERROR);
      }
    });
  }, 'image/jpeg');
}

$('#picture').on('change', function (evt) {
  var self = this;
  if (this.files) {
    if (this.files[0]) {
      loadImage(this.files[0], function(canvas) {
        upload(canvas, function() {
          $(self).val('');
          $removePicture.fadeIn();
        });
      }, {
        maxWidth: 256,
        maxHeight: 256,
        crop: true,
        orientation: true,
        canvas: true
      });
    }
  }
});

var $removePicture = $('[data-remove-picture]');

$removePicture.on('click', function(evt) {
  if (!window.confirm("Do you really want to remove your profile picture?"))
    return;
  $.ajax({
    url: '/me/picture/remove',
    type: 'POST',
    success: function(data, textStatus) {
      alert('Your profile picture has been removed.');
      $removePicture.fadeOut();
    },
    error: function() {
      alert('An error occurred when deleting your profile picture.');
    }
  });
});
