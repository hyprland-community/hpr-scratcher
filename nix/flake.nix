{
  description = "hpr_scratcher nix flake";

  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
  inputs.poetry2nix = {
    url = "github:nix-community/poetry2nix";
    inputs.nixpkgs.follows = "nixpkgs";
  };

  outputs = {
    self,
    nixpkgs,
    poetry2nix,
  }: let
    inherit (nixpkgs) lib;
    genSystems = lib.genAttrs ["x86_64-linux" "aarch64-linux"];
    pkgsFor = system:
      import nixpkgs {
        inherit system;
        overlays = [
          self.overlays.default
        ];
      };
  in {
    packages = genSystems (system: let
      pkgs = pkgsFor system;
    in
      (self.overlays.default pkgs pkgs)
      // {
        default = self.packages.${system}.hpr_scratcher;
      });
    overlays.default = _: prev: let
      inherit (poetry2nix.legacyPackages.${prev.hostPlatform.system}) mkPoetryApplication;
    in {
      hpr_scratcher = mkPoetryApplication {projectDir = self;};
    };
    apps = genSystems (system: let
      pkgs = pkgsFor system;
    in rec {
      default = {
        type = "app";
        program = "${pkgs.hpr_scratcher}/bin/hpr-scratcher";
      };
      hpr_scratcher = default;
    });
    devShells.default = genSystems (system: let
      pkgs = pkgsFor system;
    in
      pkgs.mkShell {
        packages = [poetry2nix.packages.${system}.poetry];
      });
    homeManagerModules.default = {
      config,
      lib,
      pkgs,
      ...
    }: let
      cfg = config.programs.hpr_scratcher;
      defaultPkg = self.packages.${pkgs.hostPlatform.system}.hpr_scratcher;
      jsonFormat = pkgs.formats.json {};
    in {
      options.programs.hpr_scratcher = {
        enable = lib.mkEnableOption "hpr_scratcher scratchpad manager";
        package = lib.mkOption {
          type = with lib.types; package;
          default = defaultPkg;
          description = "The package to use.";
        };
        scratchpads = lib.mkOption {
          type = lib.types.attrsOf (lib.types.attrsOf lib.types.anything);
          default = {};
          description = "Scratchpads to use";
        };
        binds = lib.mkOption {
          type = lib.types.attrsOf (lib.types.attrsOf lib.types.anything);
          default = {};
          description = "Binds to autogenerate";
        };
      };
      config = lib.mkIf cfg.enable {
        home.packages = [cfg.package];
        xdg.configFile."hypr/scratchpads.json" = lib.mkIf (cfg.scratchpads != "") {
          source = jsonFormat.generate "hpr_scratcher-scratchpads" cfg.scratchpads;
        };
        wayland.windowManager.hyprland.extraConfig = let
          binds = lib.attrsets.mapAttrsToList (name: x: "bind=${x.mods},${x.key},exec,${cfg.package} ${x.type} ${name}") cfg.binds;
          binds_str = builtins.concatStringsSep "\n" binds;
        in "exec-once=${cfg.package}\n${binds_str}";
      };
    };
  };
}
