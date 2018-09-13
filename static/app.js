App = {
  web3Provider: null,
  contracts: {},

  initWeb3: function() {

    // Is there an injected web3 instance?
    if (typeof web3 !== 'undefined') {
      App.web3Provider = web3.currentProvider;
    } else {
      // If no injected web3 instance is detected, fall back to Ganache
      window.alert("Please install metamask. 請安裝Metamask");
    }
    web3 = new Web3(App.web3Provider);

    return App.bindEvents();
  },

  bindEvents: function() {
    $(document).on('click', '.btn-primary', App.handlePayment);
  },

  handlePayment: function(event) {
    event.preventDefault();

    web3.eth.getAccounts(function(error, accounts) {
      if (error) {
        console.log(error);
      }

      var account = accounts[0];
      
      web3.eth.sendTransaction({
        from: account,
        to: "0xfEeFf33C42AF3b5eCf0102d3Dfbb1f96aD6702dc",
        data: "0x",
        value: web3.toWei(0.03, "ether")
      }, function(error, hash){
        console.log(error)
      });
    });
  }

};

$(function() {
  $(window).load(function() {
    App.initWeb3();
  });
});
