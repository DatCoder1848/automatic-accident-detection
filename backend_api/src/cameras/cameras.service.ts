import { Injectable } from '@nestjs/common';
import { PrismaService } from '../prisma/prisma.service.js';

@Injectable()
export class CamerasService {
  constructor(private prisma: PrismaService) {}

  findAll(status?: string) {
    return this.prisma.camera.findMany(status ? { where: { status: status as any } } : undefined);
  }

  findOne(id: string) {
    return this.prisma.camera.findUnique({ where: { id } });
  }

  create(data: { name: string; location: string; streamUrl: string; status?: string }) {
    return this.prisma.camera.create({ data: data as any });
  }

  update(id: string, data: { name?: string; location?: string; streamUrl?: string; status?: string }) {
    return this.prisma.camera.update({ where: { id }, data: data as any });
  }

  remove(id: string) {
    return this.prisma.camera.delete({ where: { id } });
  }
}
