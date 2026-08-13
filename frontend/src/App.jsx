import { useState } from "react";
import Nav from "./components/Nav";
import Hero from "./components/Hero";
import PropertyGrid from "./components/PropertyGrid";
import ChatWidget from "./components/ChatWidget";
import Footer from "./components/Footer";

export default function App() {
  const [prefill, setPrefill] = useState(null);

  function handleAskAbout(property) {
    setPrefill(`Tell me more about ${property.name} (${property.id})`);
    document.getElementById("assistant")?.scrollIntoView({ behavior: "smooth" });
  }

  return (
    <div>
      <Nav />
      <Hero />
      <PropertyGrid onAskAbout={handleAskAbout} />
      <ChatWidget prefill={prefill} onPrefillConsumed={() => setPrefill(null)} />
      <Footer />
    </div>
  );
}
