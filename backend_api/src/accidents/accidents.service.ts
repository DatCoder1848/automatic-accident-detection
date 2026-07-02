import { Injectable } from '@nestjs/common';
import { PrismaService } from '../prisma/prisma.service';
import { AlertsService } from '../alerts/alerts.service';

@Injectable()
export class AccidentsService {
  constructor(
    private prisma: PrismaService,
    private alertsService: AlertsService,
  ) {}

  async create(data: any) {
    const accident = await this.prisma.accident.create({ data });
    await this.alertsService.createForAccident(accident.id);
    return accident;
  }

  findAll(filters?: { severity?: string; status?: string; cameraId?: string }) {
    const where: any = {};
    if (filters?.severity) where.severity = filters.severity;
    if (filters?.status) where.status = filters.status;
    if (filters?.cameraId) where.cameraId = filters.cameraId;
    return this.prisma.accident.findMany({ where, include: { camera: true }, orderBy: { detectedAt: 'desc' } });
  }

  findOne(id: string) {
    return this.prisma.accident.findUnique({ where: { id }, include: { camera: true } });
  }

  updateStatus(id: string, status: string) {
    return this.prisma.accident.update({ where: { id }, data: { status: status as any } });
  }
}
