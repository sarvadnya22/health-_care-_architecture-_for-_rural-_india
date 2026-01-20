<<<<<<< HEAD
function nana(){
    let nipun = document.querySelector("#kaka").value
    
    console.log(nipun)
    
    if (nipun=="login")
    {
        window.open('log/login.html','blank');

    }
    else if(nipun=='admin'){
        
        window.open('admin/log_admin.html','blank',);
    }
}
function redirectToHospital() {
    const district = document.getElementById("district-select").value;
    if (district === "Nandurbar") {
        window.location.href = "https://maps.app.goo.gl/WSnEJsbU9sX4WVRJ8";
        
    } else if (district === "Ahmednagar") {
        window.location.href = "https://maps.app.goo.gl/CAauAQixejruUQn26";
    } else if (district === "Akola") {
        window.location.href = "https://maps.app.goo.gl/qjrUfyfBC7Cy722j8";
    } else if (district === "Amravati") {
        window.location.href = "https://maps.app.goo.gl/Rzi5V1ZdJ14w3BvP8";
    } else if (district === "Beed") {
        window.location.href = "https://maps.app.goo.gl/3zvtyaxDByEsJoN87";
    } else if (district === "Bhandara") {
        window.location.href = "https://maps.app.goo.gl/hqw7j4pZxaH1Yc3X9";
    } else if (district === "Buldhana") {
        window.location.href = "https://maps.app.goo.gl/xZEvJVambKnftrcC6";
    } else if (district === "Chandrapur") {
        window.location.href = "https://maps.app.goo.gl/fjhw6nQbh2ENRaU4A";
    } else if (district === "Dhule") {
        window.location.href = "https://maps.app.goo.gl/p1iqhU5iExj9Azrd8";
    } else if (district === "Gadchiroli") {
        window.location.href = "https://maps.app.goo.gl/q4TX67rVAC95zxvS7";
    } else if (district === "Gondia") {
        window.location.href = "https://maps.app.goo.gl/26sRTgeSzkqjBZrc8";
    } else if (district === "Hingoli") {
        window.location.href = "https://maps.app.goo.gl/szA96Q16J69eH3wMA";
    } else if (district === "Jalgaon") {
        window.location.href = "https://maps.app.goo.gl/qwrYJ8gmbcufB47s9";
    } else if (district === "Jalna") {
        window.location.href = "https://maps.app.goo.gl/xnPrjPWubqHSurK48";
    } else if (district === "Kolhapur") {
        window.location.href = "https://maps.app.goo.gl/5sptbkiR4sP6Bg1W7";
    } else if (district === "Latur") {
        window.location.href = "https://maps.app.goo.gl/eyDarjnpN9jBtUCC9";
    } else if (district === "Mumbai City") {
        window.location.href = "https://maps.app.goo.gl/JzUm61ufbbBcTRebA";
    } else if (district === "Mumbai Suburban") {
        window.location.href = "https://maps.app.goo.gl/5FjFNgRZTxmSQ9HR8";
    } else if (district === "Nagpur") {
        window.location.href = "https://maps.app.goo.gl/C5aKvESfwxxWeMn87";
    } else if (district === "Nanded") {
        window.location.href = "https://maps.app.goo.gl/JWDrL2U5SBKrQvyU8";
    } else if (district === "Nashik") {
        window.location.href = "https://maps.app.goo.gl/GsaVKpYac5zA9xRf7";
    } else if (district === "Dharashiv") {
        window.location.href = "https://maps.app.goo.gl/FV5vWvpgtCNxpZhRA";
    } else if (district === "Palghar") {
        window.location.href = "https://maps.app.goo.gl/ebvqWQhu4ggdKZ5D6";
    } else if (district === "Parbhani") {
        window.location.href = "https://maps.app.goo.gl/Q59AE1g8hd1kyRcB8";
    } else if (district === "Pune") {
        window.location.href = "https://maps.app.goo.gl/wtQMvxvAyG1Jvf7k9";
    } else if (district === "Raigad") {
        window.location.href = "https://maps.app.goo.gl/BbC8NAn2MzcyJo7NA";
    } else if (district === "Ratnagiri") {
        window.location.href = "https://maps.app.goo.gl/Znjr1LedBZckJ1sx8";
    } else if (district === "Sangli") {
        window.location.href = "https://maps.app.goo.gl/xwrEX6vVRb1YENra8";
    } else if (district === "Satara") {
        window.location.href = "https://maps.app.goo.gl/2Cijw1j45bpK6VoF6";
    } else if (district === "Sindhudurg") {
        window.location.href = "https://maps.app.goo.gl/eESHepPAoKmLExLk7";
    } else if (district === "Solapur") {
        window.location.href = "https://maps.app.goo.gl/4cL7cgh94S11pkhq7";
    } else if (district === "Thane") {
        window.location.href = "https://maps.app.goo.gl/7jPnFfcq3Gx3gNrX8";
    } else if (district === "Wardha") {
        window.location.href = "https://maps.app.goo.gl/DNyWvCWQJvAqPdao9";
    } else if (district === "Washim") {
        window.location.href = "https://maps.app.goo.gl/3N3hmsHGbxzTqKvk7";
    } else if (district === "Yavatmal") {
        window.location.href = "https://maps.app.goo.gl/857DJMcgfuk3g9w7A";
    } else if (district === "Sambhajinagar") {
        window.location.href = "https://maps.app.goo.gl/D5hEcpiHzxRxr1Qj9";
    } else {
        alert("Please select a valid district!");
    }
}
function lag1(){
  let b=document.getElementById("hara")
  if(b=='eng')
  {
    window.open('../english/index.html', 'blank');
  }
  else{
   
    window.open('../marathi/index.html', 'blank');
}
  }
function lag2(){
    window.open('index.html', 'blank');
}










=======
function nana(){
    let nipun = document.querySelector("#kaka").value
    
    console.log(nipun)
    
    if (nipun=="login")
    {
        window.open('log/login.html','blank');

    }
    else if(nipun=='admin'){
        
        window.open('admin/log_admin.html','blank',);
    }
}
function redirectToHospital() {
    const district = document.getElementById("district-select").value;
    if (district === "Nandurbar") {
        window.location.href = "https://maps.app.goo.gl/WSnEJsbU9sX4WVRJ8";
        
    } else if (district === "Ahmednagar") {
        window.location.href = "https://maps.app.goo.gl/CAauAQixejruUQn26";
    } else if (district === "Akola") {
        window.location.href = "https://maps.app.goo.gl/qjrUfyfBC7Cy722j8";
    } else if (district === "Amravati") {
        window.location.href = "https://maps.app.goo.gl/Rzi5V1ZdJ14w3BvP8";
    } else if (district === "Beed") {
        window.location.href = "https://maps.app.goo.gl/3zvtyaxDByEsJoN87";
    } else if (district === "Bhandara") {
        window.location.href = "https://maps.app.goo.gl/hqw7j4pZxaH1Yc3X9";
    } else if (district === "Buldhana") {
        window.location.href = "https://maps.app.goo.gl/xZEvJVambKnftrcC6";
    } else if (district === "Chandrapur") {
        window.location.href = "https://maps.app.goo.gl/fjhw6nQbh2ENRaU4A";
    } else if (district === "Dhule") {
        window.location.href = "https://maps.app.goo.gl/p1iqhU5iExj9Azrd8";
    } else if (district === "Gadchiroli") {
        window.location.href = "https://maps.app.goo.gl/q4TX67rVAC95zxvS7";
    } else if (district === "Gondia") {
        window.location.href = "https://maps.app.goo.gl/26sRTgeSzkqjBZrc8";
    } else if (district === "Hingoli") {
        window.location.href = "https://maps.app.goo.gl/szA96Q16J69eH3wMA";
    } else if (district === "Jalgaon") {
        window.location.href = "https://maps.app.goo.gl/qwrYJ8gmbcufB47s9";
    } else if (district === "Jalna") {
        window.location.href = "https://maps.app.goo.gl/xnPrjPWubqHSurK48";
    } else if (district === "Kolhapur") {
        window.location.href = "https://maps.app.goo.gl/5sptbkiR4sP6Bg1W7";
    } else if (district === "Latur") {
        window.location.href = "https://maps.app.goo.gl/eyDarjnpN9jBtUCC9";
    } else if (district === "Mumbai City") {
        window.location.href = "https://maps.app.goo.gl/JzUm61ufbbBcTRebA";
    } else if (district === "Mumbai Suburban") {
        window.location.href = "https://maps.app.goo.gl/5FjFNgRZTxmSQ9HR8";
    } else if (district === "Nagpur") {
        window.location.href = "https://maps.app.goo.gl/C5aKvESfwxxWeMn87";
    } else if (district === "Nanded") {
        window.location.href = "https://maps.app.goo.gl/JWDrL2U5SBKrQvyU8";
    } else if (district === "Nashik") {
        window.location.href = "https://maps.app.goo.gl/GsaVKpYac5zA9xRf7";
    } else if (district === "Dharashiv") {
        window.location.href = "https://maps.app.goo.gl/FV5vWvpgtCNxpZhRA";
    } else if (district === "Palghar") {
        window.location.href = "https://maps.app.goo.gl/ebvqWQhu4ggdKZ5D6";
    } else if (district === "Parbhani") {
        window.location.href = "https://maps.app.goo.gl/Q59AE1g8hd1kyRcB8";
    } else if (district === "Pune") {
        window.location.href = "https://maps.app.goo.gl/wtQMvxvAyG1Jvf7k9";
    } else if (district === "Raigad") {
        window.location.href = "https://maps.app.goo.gl/BbC8NAn2MzcyJo7NA";
    } else if (district === "Ratnagiri") {
        window.location.href = "https://maps.app.goo.gl/Znjr1LedBZckJ1sx8";
    } else if (district === "Sangli") {
        window.location.href = "https://maps.app.goo.gl/xwrEX6vVRb1YENra8";
    } else if (district === "Satara") {
        window.location.href = "https://maps.app.goo.gl/2Cijw1j45bpK6VoF6";
    } else if (district === "Sindhudurg") {
        window.location.href = "https://maps.app.goo.gl/eESHepPAoKmLExLk7";
    } else if (district === "Solapur") {
        window.location.href = "https://maps.app.goo.gl/4cL7cgh94S11pkhq7";
    } else if (district === "Thane") {
        window.location.href = "https://maps.app.goo.gl/7jPnFfcq3Gx3gNrX8";
    } else if (district === "Wardha") {
        window.location.href = "https://maps.app.goo.gl/DNyWvCWQJvAqPdao9";
    } else if (district === "Washim") {
        window.location.href = "https://maps.app.goo.gl/3N3hmsHGbxzTqKvk7";
    } else if (district === "Yavatmal") {
        window.location.href = "https://maps.app.goo.gl/857DJMcgfuk3g9w7A";
    } else if (district === "Sambhajinagar") {
        window.location.href = "https://maps.app.goo.gl/D5hEcpiHzxRxr1Qj9";
    } else {
        alert("Please select a valid district!");
    }
}
function lag1(){
  let b=document.getElementById("hara")
  if(b=='eng')
  {
    window.open('../english/index.html', 'blank');
  }
  else{
   
    window.open('../marathi/index.html', 'blank');
}
  }
function lag2(){
    window.open('index.html', 'blank');
}










>>>>>>> c3025e900aaa7513100e5c0ac0851b0b642f97bc
// chatbot