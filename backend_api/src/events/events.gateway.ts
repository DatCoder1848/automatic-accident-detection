import { WebSocketGateway, WebSocketServer } from '@nestjs/websockets';
import { Server } from 'socket.io';

@WebSocketGateway({ cors: { origin: 'http://localhost:5173' } })
export class EventsGateway {
  @WebSocketServer()
  server: Server;

  emitNewAccident(accident: any) {
    this.server.emit('new-accident', accident);
  }

  emitAccidentUpdated(accident: any) {
    this.server.emit('accident-updated', accident);
  }
}
