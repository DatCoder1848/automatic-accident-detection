import { Injectable, OnModuleInit, OnModuleDestroy } from '@nestjs/common';
import { PrismaPg } from '@prisma/adapter-pg';
import { resolve } from 'path';
import { pathToFileURL } from 'url';

@Injectable()
export class PrismaService implements OnModuleInit, OnModuleDestroy {
  private client: any;

  async onModuleInit() {
    const dbUrl = process.env.DATABASE_URL || process.env.DIRECT_URL!;
    const adapter = new PrismaPg(dbUrl);
    // Dynamic import of the ESM-only Prisma generated client
    const clientPath = resolve(process.cwd(), 'generated', 'prisma', 'client.ts');
    const mod = await import(pathToFileURL(clientPath).href);
    // tsx wraps ESM exports under module.exports
    const exports = mod['module.exports'] || mod.default || mod;
    const PrismaClient = exports.PrismaClient;
    this.client = new PrismaClient({ adapter });
    await this.client.$connect();
    console.log('[Prisma] ✅ Connected to database');
  }

  async onModuleDestroy() {
    await this.client?.$disconnect();
  }

  get user() { return this.client.user; }
  get camera() { return this.client.camera; }
  get accident() { return this.client.accident; }
  get alert() { return this.client.alert; }
}
