import React from 'react';
import './App.css';
import Navbar from "./Navbar.js";
import Dashboard from "./Dashboard.js"
import ContainerBrowser from "./ContainerBrowser"
import {
  BrowserRouter as Router,
  Switch,
  Route,
  Link
} from "react-router-dom";

function App() {
  return <Router>
    <Navbar />
    <Switch>
      <Route path="/about"></Route>
      <Route path="/browse">
        <ContainerBrowser />
      </Route>
      <Route exact path="/">
        <Dashboard />
      </Route>
    </Switch>
  </Router>;
}

export default App;
  