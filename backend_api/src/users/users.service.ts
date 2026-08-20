import { Injectable } from '@nestjs/common';
import { PrismaService } from '../prisma/prisma.service.js';

@Injectable()
export class UsersService {
  constructor(private prisma: PrismaService) {}

  findAll() {
    return this.prisma.user.findMany();
  }

  findOne(id: string) {
    return this.prisma.user.findUnique({ where: { id } });
  }

  create(data: { email: string; password: string; name?: string; role?: string }) {
    return this.prisma.user.create({ data: data as any });
  }

  update(id: string, data: { email?: string; name?: string; role?: string }) {
    return this.prisma.user.update({ where: { id }, data: data as any });
  }
}
