$(document).ready(function() {
  var socket = io.connect(location.protocol + '//' + document.domain + ':' + location.port);

  function updateBadge(selector, increment) {
    var badge = $(selector);
    var count = parseInt(badge.text()) || 0;
    count += increment;
    badge.text(count);
    if (count > 0) {
      badge.show();
    }
  }
  
  function showToast(title, message) {
    var toastId = 'toast-' + Date.now();
    var toastHTML = `
      <div id="${toastId}" class="toast" role="alert" aria-live="assertive" aria-atomic="true" data-delay="5000">
        <div class="toast-header">
          <strong class="mr-auto">${title}</strong>
          <small class="text-muted">now</small>
          <button type="button" class="ml-2 mb-1 close" data-dismiss="toast" aria-label="Close">
            <span aria-hidden="true">&times;</span>
          </button>
        </div>
        <div class="toast-body">
          ${message}
        </div>
      </div>
    `;
    $('#toast-container').append(toastHTML);
    $('#' + toastId).toast('show').on('hidden.bs.toast', function () {
      $(this).remove();
    });
  }
  
  socket.on('ticket_event', function(data) {
    console.log("Ticket Event:", data);
    updateBadge('#ticket-notification-badge', 1);
    showToast('Ticket Update', 'A ticket event has occurred. Check your dashboard.');
  });
  
  socket.on('private_message', function(data) {
    console.log("Private Message:", data);
    updateBadge('#msg-notification-badge', 1);
    showToast('New Message', 'You received a new message from ' + data.sender);
  });
  
  function refreshTicketList() {
    $.ajax({
      url: '/tickets_partial',
      method: 'GET',
      success: function(response) {
        $('#ticket-list-container').html(response);
      },
      error: function() {
        console.error("Error refreshing ticket list.");
      }
    });
  }
  
  setInterval(refreshTicketList, 60000);
});
