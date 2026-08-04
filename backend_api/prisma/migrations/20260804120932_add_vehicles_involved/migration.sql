-- AlterTable
ALTER TABLE "accidents" ADD COLUMN     "vehicles_involved" TEXT[] DEFAULT ARRAY[]::TEXT[];
