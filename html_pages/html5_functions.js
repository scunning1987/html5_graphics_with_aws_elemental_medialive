// HTML5 page function
// JAVASCRIPT
//

function getStats() {
  document.getElementById("ticker-scroller").classList.add("ticker-speed")
  current_url = window.location.href
  stats_endpoint = current_url.substring(0,current_url.lastIndexOf("/")) + "/data.json"

  var request = new XMLHttpRequest();
  request.open('GET', stats_endpoint, true);

  request.onload = function() {

  if (request.status === 200) {
    const data = JSON.parse(request.responseText);
    console.log(data)

    var utd_time_now = Math.floor(new Date() / 1000)

    if ( data["expires"]  < utd_time_now && data["expires"] > 0 ) {
      console.log("we are past expiry time to display data")
      document.getElementById("tcontainer").style.display = "none";
      document.getElementById("metric_data").style.display = "none";

    } else {

    if ( data["metrics"] != null ) {
      // Metrics data is present
      // Create dynamic table
      var tbl = document.createElement('table')
      var rows_required = Object.keys(data["metrics"]).length

      //Add the header row.
      var row = tbl.insertRow(-1);
      var table_headers = ["Key","Value"]
      var table_title = "Metric Data"
      var headerCell = document.createElement("th");
      headerCell.innerHTML = '<h1>'+table_title+'</h1>';
      headerCell.style.cssText = 'background-color: #009879;color: #ffffff;text-align: left;padding: 12px 15px;'
      headerCell.colSpan = 2
      row.appendChild(headerCell);
      /*
      for (var i = 0; i < 2; i++) {
          var headerCell = document.createElement("th");
          headerCell.innerHTML = '<h1>'+table_headers[i]+'</h1>';
          headerCell.style.cssText = 'background-color: #009879;color: #ffffff;text-align: left;padding: 12px 15px;'
          row.appendChild(headerCell);
      }*/

      //Add the data rows.
      for (var i = 0; i < rows_required; i++) {
          row = tbl.insertRow(-1);
          row.className = 'trow';

          for (var j = 0; j < 2; j++) {
            var td = row.insertCell(-1);
            td.style.cssText = 'padding: 12px 15px;'
            var metric_key = Object.keys(data["metrics"])[i]
            var metric_value = data["metrics"][metric_key]
              if ( j == 0 ) {
                td.innerHTML = '<p>'+metric_key+'</p>';
              }
              else {
                td.innerHTML = '<p>'+metric_value+'</p>';
              }
          }
      }
      document.getElementById("metric_data").innerHTML = ""
      document.getElementById("metric_data").appendChild(tbl);
      document.getElementById("metric_data").style.display = "inline-block"
    }

    if ( data['ticker'] != null ) {
      //if ( data["ticker"]["message"].length > 0 ) {
      // Ticker message is present
      document.getElementById("ticker-text").innerHTML = data["ticker"]["message"];

      // calculate ticker speed
      message_length = data["ticker"]["message"].length
      if ( message_length < 10 ) {
        console.log("Message character length doesn't meet minimum requirements, overriding to 10")
        message_length = 10
      }

      console.log("Ticker speed set to : " + data["ticker"]["speed"].toString())
      console.log("Message character length is : " + message_length.toString())

      switch(data["ticker"]["speed"]) {
        case 1:
        //
        animation_time = message_length / 1;
        break;
        case 2:
        //
        animation_time = Math.round(message_length / 1.25);
        break;
        case 3:
        //
        animation_time = Math.round(message_length / 1.5);
        break;
        case 4:
        //
        animation_time = Math.round(message_length / 1.75);
        break;
        case 5:
        animation_time = Math.round(message_length / 2);
        break;
        default:
        animation_time = message_length / 1.5
      }


      document.getElementById("ticker-scroller").setAttribute("style","animation-duration:"+animation_time.toString()+"s")

      console.log("Scroll duratiton set to " + animation_time.toString() + " seconds")

      document.getElementById("tcontainer").style.display = "inline-block";

    } else {
      document.getElementById("tcontainer").style.display = "none";
    }

   }
   } else {
    // Reached the server, but it returned an error
  }
}

request.onerror = function() {
  console.error('An error occurred fetching the JSON from ' + stats_endpoint);
};

request.send();

}

setInterval(function() {
  getStats()
}, 10000);