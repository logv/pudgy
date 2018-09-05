## pydgeon components

Pydgeon is a page component library for use with flask. The idea is to render
the page server side and automatically marshal and bring the page to life on
the client side.

## lifecycle

#### server startup

when the pydgeot blueprint initializes, it reads all classes that inherit from
Component and verifies that their packages can be built.

#### during a request

* render page on server
  * fetch data
  * render components using data
  * place components in templates
  * add relationships between components
* send to client

#### client

* receive HTML for page, load prelude.js and prelude.css
* reinstantiate components
  * display component HTML (if no CSS required)
  * load component requires
  * load component refs
  * instantiate component
  * display component HTML (if CSS required)
  * notify others that this ref has been created
