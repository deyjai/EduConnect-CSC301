import "../styles/UpcomingEventHighlight.scss";
import React from "react";

function UpcomingEvents({ event }) {
  return (
    <div className="upcoming-event">
      <div className="icon">
        <img src={event.image} alt={event.title} />
        {/* Insert SVG or image tag for the icon here */}
      </div>
      <div className="info">
        <h3>{event.title}</h3>
        <p>{event.noOfStudentsEnrolled} attending</p>
      </div>
      <button className="join-event-btn">Join</button>
      <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-arrow-right" viewBox="0 0 16 16">
        <path fill-rule="evenodd" d="M1 8a.5.5 0 0 1 .5-.5h11.793l-3.147-3.146a.5.5 0 0 1 .708-.708l4 4a.5.5 0 0 1 0 .708l-4 4a.5.5 0 0 1-.708-.708L13.293 8.5H1.5A.5.5 0 0 1 1 8" />
      </svg>
    </div>
  );
}

export default UpcomingEvents;
