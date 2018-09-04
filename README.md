## pydgeon components

The idea is to render the page server side and automatically marshal and bring
the page to life on the client side.

## component lifecycle

1. render page on server
  * fetch data
  * render components using data
  * place components in templates
  * add relationships between components
2. send to client
3. reinstantiate components
  * load component requires
  * load component refs
  * instantiate component
  * notify others that this ref has been created
4. instantiate PageController
  * (waits for all component refs?)
