import { Injectable } from '@nestjs/common';
import { PrismaService } from '../prisma/prisma.service';

@Injectable()
export class AlertsService {
  constructor(private prisma: PrismaService) {}

  async createForAccident(accidentId: string) {
    const users = await this.prisma.user.findMany();
    return this.prisma.alert.createMany({
      data: users.map((user) => ({
        accidentId,
        userId: user.id,
        type: 'NOTIFICATION',
        status: 'UNREAD',
        message: `New accident detected: ${accidentId}`,
        sentAt: new Date(),
      })),
    });
  }

  async findByUser(userId: string) {
    return this.prisma.alert.findMany({
      where: { userId },
      include: { accident: true },
    });
  }

  async findOne(id: string) {
    return this.prisma.alert.findUnique({ where: { id } });
  }

  async markAsRead(id: string) {
    return this.prisma.alert.update({
      where: { id },
      data: { status: 'READ', readAt: new Date() },
    });
  }
}
