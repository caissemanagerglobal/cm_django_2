const express = require('express');
const http = require('http');
const socketIo = require('socket.io');

const app = express();
app.use(express.json());  // Middleware to parse JSON bodies

const server = http.createServer(app);
const io = socketIo(server, {
  cors: {
    origin: "*",
    methods: ["GET", "POST"]
  }
});

io.on('connection', (socket) => {
  console.log('New client connected');
  
  socket.on('error', (error) => {
    console.log('Error occurred:', error);
  });

  socket.on('disconnect', () => {
    console.log('Client disconnected');
  });
});

// New API endpoint to receive orders from Django
app.post('/send-order', (req, res) => {
  const kdsOrderData = req.body;
  console.log('Received order data:', kdsOrderData);

  // Broadcast the received order data to all connected clients
  io.emit('update', kdsOrderData);
  
  res.status(200).send({ message: 'Order broadcasted successfully' });
});


app.post('/notify-suite-ordred', (req, res) => {
  const suiteOrdredData = req.body;
  console.log('Received suite_ordred notification:', suiteOrdredData);

  // Broadcast the received suite_ordred data to all connected clients
  io.emit('suite_ordred_update', suiteOrdredData);
  
  res.status(200).send({ message: 'suite_ordred notification broadcasted successfully' });
});

app.post('/notify-cancel-order-or-line', (req, res) => {
  const cancelData = req.body;
  console.log('Received cancellation data:', cancelData);

  // Broadcast the received cancellation data to all connected clients
  io.emit('cancel_order_or_line_update', cancelData);
  
  res.status(200).send({ message: 'Order or order line cancellation broadcasted successfully' });
});

// New API endpoint to notify about pilotage order state changes
app.post('/notify-pilotage-order-state', (req, res) => {
  const pilotageOrderStateData = req.body;
  console.log('Received pilotage order state update:', pilotageOrderStateData);

  // Broadcast the received pilotage order state update to all connected clients
  io.emit('pilotage_order_state_update', pilotageOrderStateData);
  
  res.status(200).send({ message: 'Pilotage order state update broadcasted successfully' });
});

const PORT = process.env.PORT || 4000;
server.listen(PORT, () => console.log(`Socket server running on port ${PORT}`));
