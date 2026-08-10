import { Injectable, OnModuleInit, OnModuleDestroy } from '@nestjs/common';
import { PrismaClient } from '@prisma/client';
import { PrismaPg } from '@prisma/adapter-pg';
import pg from 'pg';

@Injectable()
export class PrismaService implements OnModuleInit, OnModuleDestroy {
  private client: PrismaClient;

  constructor() {
    const connectionString = process.env.DATABASE_URL || process.env.DIRECT_URL;

    // Khởi tạo pg.Pool và ép kiểu SSL bỏ qua kiểm tra certificate
    const pool = new pg.Pool({
      connectionString,
      ssl: {
        rejectUnauthorized: false, // Bắt buộc để nhận diện self-signed cert của Supabase
      },
    });

    const adapter = new PrismaPg(pool);
    this.client = new PrismaClient({ adapter });
  }

  async onModuleInit() {
    await this.client.$connect();
    console.log('[Prisma] ✅ Connected to database');
  }

  async onModuleDestroy() {
    await this.client.$disconnect();
  }

  get user() { return this.client.user; }
  get camera() { return this.client.camera; }
  get accident() { return this.client.accident; }
  get alert() { return this.client.alert; }
}
