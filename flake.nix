{
  description = "cosmo - ???";

  inputs.flake-utils.url = "github:numtide/flake-utils";
  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-25.11";

  outputs = { self, nixpkgs, flake-utils }:
    (flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = import nixpkgs {
          inherit system;
        };

        pythonDependencies = with pkgs.python3Packages; [
            streamdeck
            pillow
            requests
            pyyaml
            python-dateutil
            poetry-core
        ];
      in
      {
        packages = {
            kimaideck = pkgs.python3Packages.buildPythonApplication rec {
              name = "kimaideck";
              src = ./.;
              pyproject = true;
              propagatedBuildInputs = pythonDependencies;

              pythonImportsCheck = [ "kimaideck" ];
            };
        };

        devShell = pkgs.mkShell {
          buildInputs = [
            pkgs.python3
            pkgs.poetry
          ] ++ pythonDependencies;
        };
      }));
}