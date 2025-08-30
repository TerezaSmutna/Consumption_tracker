function redirectToSelectedAirplane(currentURL) {
    console.log("currentUrl: " + currentURL);
    const selectedAirplaneID = document.getElementById("airplaneSelect").value;
    console.log("selectedAirplaneID: " + selectedAirplaneID);

    // Split the base_url by '/'
    const urlParts = currentURL.split('/');

    // Replace the airplane ID part with the selected airplane ID
    urlParts[2] = selectedAirplaneID;
    console.log("urlParts: " + urlParts);

    // Reconstruct the URL using only the necessary parts
    const redirectURL = urlParts.slice(0, 4).join('/');

    console.log("redirectURL: " + redirectURL);

    // Redirect to the new URL
    window.location.href = redirectURL;
  }