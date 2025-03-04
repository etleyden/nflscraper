"use client";
import './globals.css'; // Your custom styles
import Menu from "./components/menu";

export default function Home() {
  return (
    <>
      <Menu></Menu>
      <div className="flex items-center h-screen">
        <p className="mx-auto text-2xl w-5/6">
          If there is no data in the "View" tab, you probably
          still need to populate the database! Check out <code>src/pipeline</code>.
        </p>
      </div>
    </>
  );
}
