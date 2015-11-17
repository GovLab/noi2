// This was taken from bl.ocks.org/nbremer/21746a9668ffdf6d8242
// and modified a bit for NoI.

    ////////////////////////////////////////////////////////////// 
      //////////////////////// Set-Up ////////////////////////////// 
      ////////////////////////////////////////////////////////////// 

      var mScale = 1;
      var margin = {top: 100 * mScale, right: 100 * mScale,
                    bottom: 100 * mScale, left: 100 * mScale},
        width = Math.min(700, window.innerWidth - 10) - margin.left - margin.right,
        height = Math.min(width, window.innerHeight - margin.top - margin.bottom - 20);
          
      ////////////////////////////////////////////////////////////// 
      ////////////////////////// Data ////////////////////////////// 
      ////////////////////////////////////////////////////////////// 

      var levelLabels = pageConfig.RADAR_LEVEL_LABELS.reverse();

      var data = [ pageConfig.RADAR_DATA ];

      ////////////////////////////////////////////////////////////// 
      //////////////////// Draw the Chart ////////////////////////// 
      ////////////////////////////////////////////////////////////// 

      var color = d3.scale.ordinal()
        .range(["#048AB3"]);
        
      var radarChartOptions = {
        w: width,
        h: height,
        margin: margin,
        maxValue: 500,
        levels: 5,
        roundStrokes: true,
        color: color,
        labelForLevel: function(d, i) {
          return levelLabels[i];
        }
      };

      var renderChart = function() {
        RadarChart(".radarChart", data, radarChartOptions);
      };

      if ($('#overview.active').length) {
        renderChart();
      } else {
        $('a[href="#overview"]').one('shown.bs.tab', renderChart);
      }

