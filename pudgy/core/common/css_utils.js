var utils = require("common/util");

utils.inject_css("pltbi", ".pltbi { display: none; } ");

var _injected = {};
function ScopedCss(name) {
  if (!_injected[name]) {
    $P._load(name, function(m) {
      if (_injected[name]) {
        return;
      }

      utils.inject_css("scoped_"+name, m.css);
      _injected[name] = true;
    });
  }

  return "pltbi scoped_" + name;
}

function WaitForCss() {
  var args = _.toArray(arguments);
  var classes = args.map((a) => { return "wf_" + a }).join(" ");
  return "pltbi " + classes;
}

module.exports = {
  ScopedCss: ScopedCss,
  WaitForCss: WaitForCss
};
