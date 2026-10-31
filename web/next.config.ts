import type { NextConfig } from "next";

const config: NextConfig = {
  agentRules: false,
  output: process.env.NEXT_OUTPUT === "standalone" ? "standalone" : undefined, // set in web/Dockerfile
};

export default config;
