import { Injectable, OnModuleInit, OnModuleDestroy } from '@nestjs/common';
import { PrismaClient } from '../../generated/prisma/client.js';
import { PrismaPg } from '@prisma/adapter-pg';

@Injectable()
export class PrismaService implements OnModuleInit, OnModuleDestroy {
  private client: InstanceType<typeof PrismaClient>;

  constructor() {
    const adapter = new PrismaPg(process.env.DATABASE_URL!);
    this.client = new PrismaClient({ adapter });
  }

  async onModuleInit() {
    await this.client.$connect();
  }

  async onModuleDestroy() {
    await this.client.$disconnect();
  }

  get user() { return this.client.user; }
  get camera() { return this.client.camera; }
  get accident() { return this.client.accident; }
  get alert() { return this.client.alert; }
}
