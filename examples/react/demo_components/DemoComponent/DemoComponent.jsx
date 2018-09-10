var renderer = require("./external_renderer").render;

module.exports = React.createClass({
  handle_click: function(where) {
    console.log("I WAS CLICKED!", where);
  },
  render: function() {
    return <div className='outerdiv'>
      { renderer.apply(this) }
    </div>
  }
});
