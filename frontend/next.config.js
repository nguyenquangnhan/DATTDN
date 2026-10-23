/** @type {import('next').NextConfig} */
const nextConfig = {
  // Use the new stable config key for opting out packages from server component bundling
  serverExternalPackages: ["pdf2json", "cheerio"],

  webpack: (config) => {
    config.resolve.alias.canvas = false;
    config.resolve.alias.encoding = false;
    return config;
  },

  // Remove or handle 'api' options outside of this file because 'api' is not valid here
  // Instead, configure body parser in the API route file if needed

  // Optional: To silence the multiple lockfile root warning, set outputFileTracingRoot
  // const path = require('path');
  // outputFileTracingRoot: path.join(__dirname),
};

module.exports = nextConfig;
