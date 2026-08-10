import { Injectable } from '@nestjs/common';
import { PrismaService } from '../prisma/prisma.service.js';
import { AlertsService } from '../alerts/alerts.service.js';
import { EventsGateway } from '../events/events.gateway.js';

@Injectable()
export class AccidentsService {
  constructor(
    private prisma: PrismaService,
    private alertsService: AlertsService,
    private eventsGateway: EventsGateway,
  ) {}

  async create(data: any) {
    // Only pass fields that exist in the Accident model
    const { cameraId, incidentId, confidence, severity, description, detectedAt, videoClipUrl, thumbnailUrl, vehiclesInvolved, latitude, longitude } = data;
    const cleanData: any = { cameraId, confidence, severity };
    if (incidentId) cleanData.incidentId = incidentId;
    if (description) cleanData.description = description;
    if (detectedAt) cleanData.detectedAt = new Date(detectedAt);
    if (videoClipUrl) cleanData.videoClipUrl = videoClipUrl;
    if (thumbnailUrl) cleanData.thumbnailUrl = thumbnailUrl;
    if (vehiclesInvolved) cleanData.vehiclesInvolved = vehiclesInvolved;
    if (latitude != null) cleanData.latitude = latitude;
    if (longitude != null) cleanData.longitude = longitude;

    const accident = await this.prisma.accident.create({ data: cleanData });
    await this.alertsService.createForAccident(accident.id);
    this.eventsGateway.emitNewAccident(accident);
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
    return this.prisma.accident.findUnique({ where: { id }, include: { camera: true, alerts: true } });
  }

  async updateStatus(id: string, status: string) {
    const accident = await this.prisma.accident.update({ where: { id }, data: { status: status as any } });
    this.eventsGateway.emitAccidentUpdated(accident);
    return accident;
  }
}
