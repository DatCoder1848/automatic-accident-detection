import 'dotenv/config';
import { PrismaClient } from '../generated/prisma/client.js';
import { PrismaPg } from '@prisma/adapter-pg';
import * as bcrypt from 'bcrypt';

const adapter = new PrismaPg(process.env.DIRECT_URL!);
const prisma = new PrismaClient({ adapter });

async function main() {
  const hash = (pw: string) => bcrypt.hashSync(pw, 10);

  await prisma.user.upsert({
    where: { email: 'admin@system.com' },
    update: {},
    create: { email: 'admin@system.com', password: hash('admin123'), name: 'Admin', role: 'ADMIN' },
  });

  await prisma.user.upsert({
    where: { email: 'operator@system.com' },
    update: {},
    create: { email: 'operator@system.com', password: hash('operator123'), name: 'Operator', role: 'OPERATOR' },
  });

  const count = await prisma.camera.count();
  if (count === 0) {
    await prisma.camera.createMany({
      data: [
        { name: 'Camera Ngã Tư Sở', location: 'Ngã Tư Sở, Hà Nội', streamUrl: 'rtsp://192.168.1.10/stream1', status: 'ACTIVE' },
        { name: 'Camera Cầu Giấy', location: 'Cầu Giấy, Hà Nội', streamUrl: 'rtsp://192.168.1.11/stream1', status: 'ACTIVE' },
        { name: 'Camera Trần Duy Hưng', location: 'Trần Duy Hưng, Hà Nội', streamUrl: 'rtsp://192.168.1.12/stream1', status: 'ACTIVE' },
        { name: 'Camera Phạm Hùng', location: 'Phạm Hùng, Hà Nội', streamUrl: 'rtsp://192.168.1.13/stream1', status: 'MAINTENANCE' },
      ],
    });
  }

  console.log('Seed completed!');
}

main().catch(console.error).finally(() => prisma.$disconnect());
