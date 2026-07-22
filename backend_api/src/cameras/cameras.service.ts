import { Injectable } from '@nestjs/common';
import { PrismaService } from '../prisma/prisma.service';
import { CameraStatus } from '@prisma/client'; //from '../../generated/prisma/client.js';

@Injectable()
export class CamerasService {
  constructor(private prisma: PrismaService) {}

  findAll(status?: CameraStatus) {
    return this.prisma.camera.findMany(status ? { where: { status } } : undefined);
  }

  findOne(id: string) {
    return this.prisma.camera.findUnique({ where: { id } });
  }

  create(data: { name: string; location: string; streamUrl: string; status?: CameraStatus }) {
    return this.prisma.camera.create({ data });
  }

  update(id: string, data: { name?: string; location?: string; streamUrl?: string; status?: CameraStatus }) {
    return this.prisma.camera.update({ where: { id }, data });
  }

  remove(id: string) {
    return this.prisma.camera.delete({ where: { id } });
  }
}
