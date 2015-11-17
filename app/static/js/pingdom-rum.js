if (globalConfig.PINGDOM_RUM_ID) {
  var _prum = [['id', globalConfig.PINGDOM_RUM_ID],
               ['mark', 'firstbyte', (new Date()).getTime()]];
  (function() {
    var s = document.getElementsByTagName('script')[0]
      , p = document.createElement('script');
    p.async = 'async';
    p.src = '//rum-static.pingdom.net/prum.min.js';
    s.parentNode.insertBefore(p, s);
  })();
}
